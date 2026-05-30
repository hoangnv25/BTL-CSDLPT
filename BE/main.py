from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import asyncio

from BE.database import Base, SessionLocal, engine, engines, circuit_breaker
import BE.models  # noqa: F401  # register ORM metadata
from BE.routers.category import router as category_router
from BE.routers.inventory import router as inventory_router
from BE.routers.product import router as product_router
from BE.routers.user import router as user_router
from BE.routers.warehouse import router as warehouse_router
from BE.routers.order import router as order_router
from BE.routers.package import router as package_router
from BE.routers.websocket import router as websocket_router
from BE.routers.replication import router as replication_router
from BE.routers.replication import initial_full_sync
from BE.workers.replication_worker import replication_worker

app = FastAPI(title="FastAPI + MySQL + Docker")

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
app.include_router(websocket_router)
app.include_router(replication_router)

@app.on_event("startup")
async def on_startup() -> None:
    import asyncio
    app.state.loop = asyncio.get_running_loop()
    from BE.utils.migration import migrate_main_inventories_to_shards
    print("Khởi tạo cấu trúc bảng cho toàn bộ CSDL Phân tán...")
    
    # 1. Tạo tất cả các bảng ở Main DB (Trung tâm), ngoại trừ inventories, packages, và package_details
    if "main" in engines:
        try:
            main_tables = [
                table for name, table in Base.metadata.tables.items()
                if name not in ["inventories", "packages", "package_details"]
            ]
            Base.metadata.create_all(bind=engines["main"], tables=main_tables)
            print("Đã khởi tạo toàn bộ cấu trúc bảng cho Main DB (ngoại trừ inventories, packages, package_details).")
        except Exception as e:
            print(f"Error: Không thể khởi tạo bảng cho Main DB: {e}")
            
    # 2. Tạo cấu trúc bảng cho các Node chi nhánh và xóa bảng không cần thiết
    DISTRIBUTED_TABLE_NAMES = ["categories", "products", "inventories", "packages", "package_details"]
    
    node_tables = [
        table for name, table in Base.metadata.tables.items()
        if name in DISTRIBUTED_TABLE_NAMES
    ]
    
    def setup_node_tables(site_name: str, db_engine) -> bool:
        if not circuit_breaker.is_available(site_name):
            print(f"Circuit Breaker: Bỏ qua tạo bảng cho Node [{site_name}] do đang OFFLINE.")
            return False
        try:
            # 2a. Tạo các bảng cần thiết
            Base.metadata.create_all(bind=db_engine, tables=node_tables)
            print(f"Đã khởi tạo cấu trúc bảng phân tán cho Node: {site_name}")
            
            # 2b. Dọn dẹp và xóa toàn bộ bảng không cần thiết trên Node phụ
            from sqlalchemy import inspect
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
    done, not_done = wait(futures.keys(), timeout=0.5)
    
    for f in done:
        pass
        
    for f in not_done:
        site_name = futures[f]
        circuit_breaker.mark_failure(site_name)
        print(f"Warning: Quá trình tạo/dọn dẹp bảng cho {site_name} quá hạn 0.5s. Đánh dấu OFFLINE.")

    # 3. Chạy di trú và kiểm tra đối chiếu tồn kho/kiện hàng từ main DB sang các Node phân sharding
    try:
        from BE.utils.migration import (
            verify_and_initialize_missing_inventories,
            migrate_main_packages_to_shards
        )
        migrate_main_inventories_to_shards()
        verify_and_initialize_missing_inventories()
        migrate_main_packages_to_shards()
    except Exception as e:
        print(f"Error: Lỗi khi di trú/bù đắp dữ liệu trong quá trình startup: {e}")
    
    # Run initial full sync in background thread
    print("Khởi chạy đồng bộ toàn phần trong background...")
    asyncio.create_task(asyncio.to_thread(initial_full_sync))
    
    # Start replication worker in background
    print("Khởi chạy worker đồng bộ...")
    asyncio.create_task(replication_worker.run())


@app.get("/")
def root():
    return {"message": "FastAPI is running with MySQL in Docker"}


@app.get("/health/db")
def health_db():
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}
