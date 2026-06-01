import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

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
        # Cấu hình timeout kết nối (2.0 giây) để tránh treo Backend khi một Node phụ bị sập
        engines[site] = create_engine(
            url, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2.0}
        )
        SessionLocals[site] = sessionmaker(autocommit=False, autoflush=False, bind=engines[site])

# Mặc định sẽ lấy db trung tâm
engine = engines.get("main")
if engine is None:
    # Dự phòng khởi tạo từ DATABASE_URL nếu MAIN_DB_URL rỗng
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
