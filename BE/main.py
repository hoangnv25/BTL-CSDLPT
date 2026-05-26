from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import asyncio

from BE.database import Base, SessionLocal, engine, engines
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
    print("Khởi tạo cấu trúc bảng cho toàn bộ CSDL Phân tán...")
    
    # 1. Tạo tất cả các bảng ở Main DB (Trung tâm)
    if "main" in engines:
        try:
            Base.metadata.create_all(bind=engines["main"])
            print("Đã khởi tạo toàn bộ cấu trúc bảng cho Main DB.")
        except Exception as e:
            print(f"Error: Không thể khởi tạo bảng cho Main DB: {e}")
            
    # 2. Tạo cấu trúc bảng cho các Node chi nhánh (Chỉ các bảng được chỉ định phân tán/nhân bản)
    # Hiện tại chỉ có bảng 'categories' được nhân bản, sau này muốn thêm bảng nào chỉ cần thêm tên bảng vào đây.
    DISTRIBUTED_TABLE_NAMES = ["categories"]
    
    node_tables = [
        table for name, table in Base.metadata.tables.items()
        if name in DISTRIBUTED_TABLE_NAMES
    ]
    
    for site_name, db_engine in engines.items():
        if site_name == "main":
            continue
        try:
            Base.metadata.create_all(bind=db_engine, tables=node_tables)
            print(f"Đã khởi tạo cấu trúc bảng phân tán cho Node: {site_name}")
        except Exception as e:
            print(f"Warning: Không thể tạo bảng cho {site_name}: {e}")
    
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
