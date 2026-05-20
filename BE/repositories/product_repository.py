from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from BE.models.product import Product

class ProductRepository:
    @staticmethod
    def create(
        session: Session,
        *,
        name: str,
        category_id: int,
        price: Decimal,
    ) -> Product:
        row = Product(
            name=name,
            category_id=category_id,
            price=price,
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[Product]:
        stmt = select(Product).order_by(Product.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_category(session: Session, category_id: int) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.category_id == category_id)
            .order_by(Product.id)
        )
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, id: int) -> Product | None:
        stmt = select(Product).where(Product.id == id)
        return session.scalar(stmt)

    @staticmethod
    def update(
        row: Product,
        *,
        name: str,
        category_id: int,
        price: Decimal,
    ) -> Product:
        row.name = name
        row.category_id = category_id
        row.price = price
        return row
