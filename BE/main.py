from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect
import asyncio
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from BE.database import Base, SessionLocal, engine, engines, circuit_breaker
import BE.models  # noqa: F401  # register ORM metadata
from BE.routers.category import router as category_router
from BE.routers.inventory import router as inventory_router
from BE.routers.product import router as product_router
from BE.routers.user import router as user_router
from BE.routers.warehouse import router as warehouse_router
from BE.routers.order import router as order_router
from BE.routers.package import router as package_router
from BE.routers.stats import router as stats_router
from BE.routers.websocket import router as websocket_router
from BE.routers.replication import router as replication_router
from BE.routers.replication import initial_full_sync
from BE.workers.replication_worker import replication_worker

async def schedule_stats_sync():
    """Vòng lặp chạy đồng bộ thống kê định kỳ dựa trên cấu hình ở .env (Múi giờ Việt Nam GMT+7)"""
    from BE.services.stats_service import StatsService
    import os
    
    tz_vn = timezone(timedelta(hours=7))
    sync_time_str = os.getenv("STATS_SYNC_TIME", "01:00")
    try:
        hour_str, minute_str = sync_time_str.split(":")
        sync_hour = int(hour_str)
        sync_minute = int(minute_str)
    except Exception as e:
        print(f"[DailyStats] Lỗi cấu hình STATS_SYNC_TIME ({sync_time_str}), fallback về 01:00: {e}")
        sync_hour = 1
        sync_minute = 0

    while True:
        now = datetime.now(tz_vn)
        target = now.replace(hour=sync_hour, minute=sync_minute, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        
        sleep_seconds = (target - now).total_seconds()
        print(f"[DailyStats] Nhiệm vụ đồng bộ được lên lịch vào: {target.strftime('%Y-%m-%d %H:%M:%S')} (Múi giờ VN, nghỉ {sleep_seconds/3600:.2f} giờ)")
        
        await asyncio.sleep(sleep_seconds)
        
        try:
            # Chạy logic tổng hợp
            StatsService.sync_all_stats_to_central()
        except Exception as e:
            print(f"[DailyStats] Lỗi khi chạy đồng bộ định kỳ: {e}")


async def heartbeat_check_nodes():
    """Vòng lặp ngầm kiểm tra sức khỏe của các Node DB mỗi 5 giây"""
    from BE.database import engines, circuit_breaker
    
    def check_nodes():
        for node_name, engine in engines.items():
            if node_name == "main":
                continue
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                if not circuit_breaker.is_online(node_name):
                    circuit_breaker.mark_success(node_name)
                    print(f"[Heartbeat] Node {node_name.upper()} đã hoạt động trở lại. Đánh dấu ONLINE.")
            except Exception:
                if circuit_breaker.is_online(node_name):
                    circuit_breaker.mark_failure(node_name)
                    print(f"[Heartbeat] Node {node_name.upper()} gặp sự cố. Đánh dấu OFFLINE.")
                
    while True:
        await asyncio.sleep(5.0)
        await asyncio.to_thread(check_nodes)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    app.state.loop = asyncio.get_running_loop()
    from BE.utils.migration import migrate_main_inventories_to_shards
    print("Khởi tạo cấu trúc bảng cho toàn bộ CSDL Phân tán...")
    
    # Kích hoạt worker đồng bộ thống kê định kỳ
    asyncio.create_task(schedule_stats_sync())
    # Kích hoạt heartbeat kiểm tra sức khỏe các node phụ
    asyncio.create_task(heartbeat_check_nodes())

    # 1. Tạo tất cả các bảng ở Main DB (Trung tâm), ngoại trừ dữ liệu phân mảnh (inventories, packages,...)
    if "main" in engines:
        try:
            main_tables = [
                table for name, table in Base.metadata.tables.items()
                if name not in ["inventories", "packages", "package_details", "warehouses"]
            ]
            Base.metadata.create_all(bind=engines["main"], tables=main_tables)
            print("Đã khởi tạo toàn bộ cấu trúc bảng cho Main DB (ngoại trừ dữ liệu sharding tồn kho/kiện hàng/kho hàng).")

        except Exception as e:
            print(f"Error: Không thể khởi tạo bảng cho Main DB: {e}")
            
    # 2. Tạo cấu trúc bảng cho các Node chi nhánh và xóa bảng không cần thiết
    # Lưu ý: categories và products được giữ lại ở Node để thực hiện join dữ liệu local (Read-replicated)
    # warehouses được phân mảnh nguyên thủy (PHF) trên các Node phụ
    DISTRIBUTED_TABLE_NAMES = ["warehouses", "categories", "products", "inventories", "packages", "package_details"]
    
    node_tables = [
        table for name, table in Base.metadata.tables.items()
        if name in DISTRIBUTED_TABLE_NAMES
    ]
    
    def setup_node_tables(site_name: str, db_engine) -> bool:
        if not circuit_breaker.is_available(site_name):
            print(f"Circuit Breaker: Bỏ qua tạo bảng cho Node [{site_name}] do đang OFFLINE.")
            return False
        try:
            # 2a. Tạo các bảng cần thiết (SQLAlchemy sẽ tạo những bảng còn thiếu)
            Base.metadata.create_all(bind=db_engine, tables=node_tables)
            
            # 2b. Đồng bộ cấu trúc bảng và vá dữ liệu
            with db_engine.begin() as conn:
                inspector = inspect(db_engine) # Refresh inspector
                # 1. Xử lý bảng packages (Thêm cột delivered_at nếu chưa tồn tại theo yêu cầu mới)
                columns_pkg = [c['name'] for c in inspector.get_columns('packages')]
                if 'delivered_at' not in columns_pkg:
                    conn.execute(text("ALTER TABLE packages ADD COLUMN delivered_at DATETIME NULL;"))
                    print(f"Đã thêm cột delivered_at vào bảng packages trên Node: {site_name}")
            
            # 2c. Dọn dẹp và xóa toàn bộ bảng không cần thiết trên Node phụ
            inspector = inspect(db_engine)
            existing_tables = inspector.get_table_names()
            for tbl in existing_tables:
                if tbl not in DISTRIBUTED_TABLE_NAMES:
                    with db_engine.begin() as conn:
                        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                        conn.execute(text(f"DROP TABLE IF EXISTS `{tbl}`;"))
                        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    print(f"Đã xóa bảng không cần thiết `{tbl}` trên Node: {site_name}")
            return True
        except Exception as e:
            circuit_breaker.mark_failure(site_name)
            print(f"Warning: Không thể quản lý cấu trúc bảng cho {site_name}: {e}")
            return False

    # Chạy song song tạo bảng cho các site nhánh để tránh block luồng chính
    from concurrent.futures import ThreadPoolExecutor, wait
    startup_pool = ThreadPoolExecutor(max_workers=3)
    
    futures = {
        startup_pool.submit(setup_node_tables, site_name, db_engine): site_name
        for site_name, db_engine in engines.items()
        if site_name != "main"
    }
    # Tăng timeout lên 30s để đảm bảo các DB Node kịp khởi động và chạy ALTER TABLE
    done, not_done = wait(futures.keys(), timeout=30.0)
    
    for f in done:
        pass
        
    for f in not_done:
        site_name = futures[f]
        circuit_breaker.mark_failure(site_name)
        print(f"Warning: Quá trình tạo/dọn dẹp bảng cho {site_name} quá hạn 0.5s. Đánh dấu OFFLINE.")

    # 3. Chạy di trú và kiểm tra đối chiếu tồn kho/kiện hàng từ main DB sang các Node phân sharding
    try:
        from BE.utils.migration import (
            migrate_warehouses_to_shards,
            setup_node_foreign_keys,
            verify_and_initialize_missing_inventories,
            migrate_main_packages_to_shards
        )
        # 3a. Di trú kho hàng sang các phân mảnh phụ trước
        migrate_warehouses_to_shards()
        
        # 3b. Thiết lập khóa ngoại vật lý tại các Node chi nhánh
        for site_name, db_engine in engines.items():
            if site_name != "main" and circuit_breaker.is_available(site_name):
                setup_node_foreign_keys(site_name, db_engine)

        # 3c. Tiếp tục di trú tồn kho và kiện hàng
        migrate_main_inventories_to_shards()
        verify_and_initialize_missing_inventories()
        migrate_main_packages_to_shards()
    except Exception as e:
        print(f"Di trú dữ liệu thất bại: {e}")

    # 4. Chạy đồng bộ toàn phần ban đầu trong luồng nền
    print("Khởi chạy đồng bộ toàn phần trong background...")
    asyncio.create_task(asyncio.to_thread(initial_full_sync))
    
    # 5. Khởi chạy worker đồng bộ trong background
    print("Khởi chạy worker đồng bộ...")
    worker_task = asyncio.create_task(replication_worker.run())
    
    yield
    
    # Tắt app: Dừng worker
    print("Đang tắt ứng dụng, dừng worker đồng bộ...")
    worker_task.cancel()

app = FastAPI(title="FastAPI + MySQL + Docker", lifespan=lifespan)

# Cấu hình CORS để cho phép Frontend (cổng 5173) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn hoặc bạn có thể thay thế bằng ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(warehouse_router)
app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(package_router, prefix="/package", tags=["Package"])
app.include_router(stats_router, prefix="/stats", tags=["Statistics"])
app.include_router(websocket_router)
app.include_router(replication_router)

@app.get("/")
def root():
    return {"message": "FastAPI is running with MySQL in Docker"}


@app.get("/health/db")
def health_db():
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}
