from sqlalchemy import select
from sqlalchemy.orm import Session
from BE.models.category import Category

class CategoryRepository:
    @staticmethod
    def create(session: Session, *, name: str) -> Category:
        row = Category(name=name)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[Category]:
        stmt = select(Category).order_by(Category.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, id: int) -> Category | None:
        stmt = select(Category).where(Category.id == id)
        return session.scalar(stmt)

    @staticmethod
    def update(row: Category, *, name: str) -> Category:
        row.name = name
        return row

    @staticmethod
    def delete(session: Session, row: Category) -> None:
        session.delete(row)
