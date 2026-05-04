from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.models import User

app = FastAPI(title="FastAPI + MySQL + Docker")


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


@app.post("/users/{name}")
def create_user(name: str):
    with SessionLocal() as session:
        user = User(name=name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return {"id": user.id, "name": user.name}
