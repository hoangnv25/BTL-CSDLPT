from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
import app.models  # noqa: F401  # register ORM metadata
from app.routers.category import router as category_router
from app.routers.inventory import router as inventory_router
from app.routers.product import router as product_router
from app.routers.user import router as user_router
from app.routers.warehouse import router as warehouse_router
from app.routers.order import router as order_router

app = FastAPI(title="FastAPI + MySQL + Docker")
app.include_router(user_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(warehouse_router)
app.include_router(inventory_router)
app.include_router(order_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "FastAPI is running with MySQL in Docker"}


@app.get("/health/db")
def health_db():
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}
