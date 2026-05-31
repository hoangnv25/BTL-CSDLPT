from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect
import asyncio
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    from BE.utils.migration import migrate_main_inventories_to_shards
    print("Khởi tạo cấu trúc bảng cho toàn bộ CSDL Phân tán...")
    
    # 1. Tạo tất cả các bảng ở Main DB (Trung tâm), ngoại trừ dữ liệu phân mảnh (inventories, packages, stats,...)
    if "main" in engines:
        try:
            main_tables = [
                table for name, table in Base.metadata.tables.items()
                if name not in ["inventories", "packages", "package_details", "package_sales_stats", "warehouses"]
            ]
            Base.metadata.create_all(bind=engines["main"], tables=main_tables)
            print("Đã khởi tạo toàn bộ cấu trúc bảng cho Main DB (ngoại trừ dữ liệu phân sharding).")

        except Exception as e:
            print(f"Error: Không thể khởi tạo bảng cho Main DB: {e}")
            
    # 2. Tạo cấu trúc bảng cho các Node chi nhánh và xóa bảng không cần thiết
    # Lưu ý: categories và products được giữ lại ở Node để thực hiện join dữ liệu local (Read-replicated)
    # warehouses được phân mảnh nguyên thủy (PHF) trên các Node phụ
    DISTRIBUTED_TABLE_NAMES = ["warehouses", "categories", "products", "inventories", "packages", "package_details", "package_sales_stats"]
    
    node_tables = [
        table for name, table in Base.metadata.tables.items()
        if name in DISTRIBUTED_TABLE_NAMES
    ]
    
    def setup_node_tables(site_name: str, db_engine) -> bool:
        if not circuit_breaker.is_available(site_name):
            print(f"Circuit Breaker: Bỏ qua tạo bảng cho Node [{site_name}] do đang OFFLINE.")
            return False
        try:
            # 2a. Xử lý di trú tên bảng TRƯỚC khi SQLAlchemy create_all tạo bảng mới
            inspector = inspect(db_engine)
            existing_tables = inspector.get_table_names()
            
            with db_engine.begin() as conn:
                # Đổi tên product_sales_stats -> package_sales_stats nếu bảng cũ tồn tại và bảng mới chưa có
                if 'product_sales_stats' in existing_tables and 'package_sales_stats' not in existing_tables:
                    conn.execute(text("RENAME TABLE product_sales_stats TO package_sales_stats;"))
                    print(f"[Migration] Đã đổi tên bảng product_sales_stats -> package_sales_stats trên Node: {site_name}")
            
            # 2b. Tạo các bảng cần thiết (SQLAlchemy sẽ tạo những bảng còn thiếu)
            Base.metadata.create_all(bind=db_engine, tables=node_tables)
            
            # 2c. Đồng bộ cấu trúc bảng và vá dữ liệu
            with db_engine.begin() as conn:
                inspector = inspect(db_engine) # Refresh inspector
                # 1. Xử lý bảng packages (Xóa cột delivered_at nếu tồn tại theo yêu cầu mới)
                columns_pkg = [c['name'] for c in inspector.get_columns('packages')]
                if 'delivered_at' in columns_pkg:
                    conn.execute(text("ALTER TABLE packages DROP COLUMN delivered_at;"))
                    print(f"Đã xóa cột delivered_at khỏi bảng packages trên Node: {site_name}")
                
                # 2. Xử lý bảng thống kê
                columns_stats = [c['name'] for c in inspector.get_columns('package_sales_stats')]
                
                # Thêm các cột nếu thiếu
                if 'package_count' not in columns_stats:
                    conn.execute(text("ALTER TABLE package_sales_stats ADD COLUMN package_count INT NOT NULL DEFAULT 0;"))
                if 'revenue' not in columns_stats:
                    conn.execute(text("ALTER TABLE package_sales_stats ADD COLUMN revenue DOUBLE NOT NULL DEFAULT 0;"))

                # --- PHỤC HỒI DỮ LIỆU THỐNG KÊ TỪ CÁC KIỆN HÀNG ĐÃ GIAO ---
                # 1. Lấy danh sách các kiện hàng đã giao nhưng chưa có trong stats
                # Chúng ta sẽ sử dụng created_at để tạm làm ngày giao cho dữ liệu cũ
                conn.execute(text("""
                    INSERT INTO package_sales_stats (product_id, warehouse_id, delivered_at, quantity, revenue, package_count)
                    SELECT 
                        pd.product_id, 
                        p.warehouse_id, 
                        DATE(p.created_at) as del_date,
                        SUM(pd.quantity) as qty,
                        SUM(pd.quantity * prod.price) as rev,
                        0 as pkg_c
                    FROM packages p
                    JOIN package_details pd ON p.id = pd.package_id
                    JOIN products prod ON pd.product_id = prod.id
                    WHERE p.status = 'Delivered'
                    GROUP BY pd.product_id, p.warehouse_id, del_date
                    ON DUPLICATE KEY UPDATE 
                        quantity = quantity, 
                        revenue = revenue;
                """))

                # 2. Vá package_count (Chỉ đếm 1 kiện hàng 1 lần)
                # Cách làm: Với mỗi package ID, chọn 1 product_id bất kỳ để gán package_count = 1
                conn.execute(text("""
                    UPDATE package_sales_stats s
                    JOIN (
                        SELECT 
                            pd.product_id, 
                            p.warehouse_id, 
                            DATE(p.created_at) as del_date,
                            COUNT(DISTINCT p.id) as real_pkg_count
                        FROM packages p
                        JOIN package_details pd ON p.id = pd.package_id
                        WHERE p.status = 'Delivered'
                        AND pd.id IN (
                            SELECT MIN(id) FROM package_details GROUP BY package_id
                        )
                        GROUP BY pd.product_id, p.warehouse_id, del_date
                    ) AS src ON s.product_id = src.product_id 
                        AND s.warehouse_id = src.warehouse_id 
                        AND s.delivered_at = src.del_date
                    SET s.package_count = src.real_pkg_count;
                """))
                print(f"[Migration] Đã phục hồi dữ liệu thống kê từ {site_name}")
            
            # 2d. Dọn dẹp và xóa toàn bộ bảng không cần thiết trên Node phụ
            inspector = inspect(db_engine)
            existing_tables = inspector.get_table_names()
            for tbl in existing_tables:
                if tbl not in DISTRIBUTED_TABLE_NAMES and tbl != 'product_sales_stats':
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
