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
    "central": DATABASE_URL,
    "north": build_node_url("NORTH_DB"),
    "central_region": build_node_url("CENTRAL_REGION_DB"),
    "south": build_node_url("SOUTH_DB"),
}

engines = {}
SessionLocals = {}

for site, url in DB_URLS.items():
    if url:
        engines[site] = create_engine(url, pool_pre_ping=True)
        SessionLocals[site] = sessionmaker(autocommit=False, autoflush=False, bind=engines[site])

# Default sẽ lấy db trung tâm
engine = engines.get("central")
if engine is None:
    # Fallback to create from DATABASE_URL if CENTRAL_DB_URL was somehow empty and DATABASE_URL failed
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocals["central"] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = SessionLocals["central"]

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Get default database session (Central). Used by existing APIs."""
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
