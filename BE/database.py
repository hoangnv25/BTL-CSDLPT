import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv(override=True)

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# Default database URL Trung tâm
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

def build_node_url(prefix: str):
    host = os.getenv(f"{prefix}_HOST")
    if not host:
        return None
    port = os.getenv(f"{prefix}_PORT", "3306")
    user = os.getenv(f"{prefix}_USER", "root")
    password = os.getenv(f"{prefix}_PASSWORD", "")
    db_name = os.getenv(f"{prefix}_DB", "")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

# Multi-DB Phân tán
DB_URLS = {
    "main": DATABASE_URL,
    "north": build_node_url("NORTH_DB"),
    "central": build_node_url("CENTRAL_DB"),
    "south": build_node_url("SOUTH_DB"),
}

import time
from threading import Lock

class NodeCircuitBreaker:
    def __init__(self):
        self._states = {} # {node: {"status": "ONLINE", "last_failure": 0}}
        self._lock = Lock()
        self.COOLDOWN = 10 # 10 giây hồi chiêu trước khi thử lại một node đang sập

    def is_available(self, node: str) -> bool:
        with self._lock:
            state = self._states.setdefault(node, {"status": "ONLINE", "last_failure": 0})
            if state["status"] == "OFFLINE":
                if time.time() - state["last_failure"] > self.COOLDOWN:
                    return True
                return False
            return True

    def is_online(self, node: str) -> bool:
        with self._lock:
            state = self._states.setdefault(node, {"status": "ONLINE", "last_failure": 0})
            return state["status"] == "ONLINE"

    def mark_failure(self, node: str):
        with self._lock:
            state = self._states.setdefault(node, {"status": "ONLINE", "last_failure": 0})
            state["status"] = "OFFLINE"
            state["last_failure"] = time.time()

    def mark_success(self, node: str):
        with self._lock:
            state = self._states.setdefault(node, {"status": "ONLINE", "last_failure": 0})
            state["status"] = "ONLINE"

# Global Circuit Breaker instance
circuit_breaker = NodeCircuitBreaker()

engines = {}
SessionLocals = {}

for site, url in DB_URLS.items():
    if url:
        engines[site] = create_engine(
            url, 
            pool_pre_ping=(site == "main"),
            pool_size=30,
            max_overflow=20,
            pool_timeout=10,
            connect_args={"connect_timeout": 0.5}
        )
        SessionLocals[site] = sessionmaker(autocommit=False, autoflush=False, bind=engines[site])

# Mặc định sẽ lấy db trung tâm
engine = engines.get("main")
if engine is None:
    # Dự phòng khởi tạo từ DATABASE_URL nếu MAIN_DB_URL rỗng
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        pool_size=30,
        max_overflow=20,
        pool_timeout=10
    )
    SessionLocals["main"] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = SessionLocals["main"]

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Lấy session DB mặc định (Main). Sử dụng cho các API hiện có."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_node(node_name: str) -> Session:
    """Get database session for a specific node. Used by workers/sync."""
    if node_name not in SessionLocals:
        raise ValueError(f"Database node '{node_name}' is not configured.")
    return SessionLocals[node_name]()

from fastapi import Request
from sqlalchemy import text
import random
import asyncio

def get_read_db(request: Request) -> Generator[Session, None, None]:
    """Smart Read Routing Strategy cho Khách hàng và Admin Kho"""
    target_node = request.headers.get("X-Target-Node", "main").lower()
    
    if target_node == "main":
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
        return
        
    nodes_to_try = []
    
    if target_node == "auto":
        nodes_to_try = ["north", "central", "south"]
        random.shuffle(nodes_to_try)
        
    for node in nodes_to_try:
        if circuit_breaker.is_available(node):
            db = SessionLocals.get(node)
            if db:
                session = db()
                try:
                    yield session
                    circuit_breaker.mark_success(node)
                    return
                except Exception as e:
                    # Phát hiện lỗi trong lúc thực hiện truy vấn (node sập hoặc lỗi mạng)
                    circuit_breaker.mark_failure(node)
                    print(f"[Read Routing] Phát hiện lỗi kết nối/truy vấn trên Node {node}! Đang đánh dấu OFFLINE...")
                    
                    # Bắn thông báo WebSocket cảnh báo cho Admin
                    try:
                        from BE.routers.websocket import manager
                        loop = request.app.state.loop
                        msg = {
                            "type": "SYNC_ERROR",
                            "message": f"Phát hiện Node {node.upper()} gặp sự cố khi truy xuất dữ liệu! Hệ thống đã cô lập node này."
                        }
                        asyncio.run_coroutine_threadsafe(manager.broadcast(msg), loop)
                    except Exception as ws_err:
                        print("Không thể gửi WS cảnh báo:", ws_err)
                    
                    # Ném tiếp exception ra ngoài để FastAPI báo lỗi cho client và không treo generator
                    raise e
                finally:
                    session.close()
                    
    # Nếu tất cả các node đều sập hoặc không khả dụng -> Fallback an toàn về Main
    print(f"[Read Routing] Cảnh báo: TẤT CẢ các Node chi nhánh đã sập! Bẻ lái truy cập về MAIN DB.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
