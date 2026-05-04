from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.inventory import Inventory

class InventoryRepository:
    @staticmethod
    def create(session: Session, *, product_id: int, warehouse_id: int, stock_quantity: int = 0) -> Inventory:
        row = Inventory(
            product_id=product_id,
            warehouse_id=warehouse_id,
            stock_quantity=stock_quantity,
            updated_at=datetime.utcnow()
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[Inventory]:
        stmt = select(Inventory).order_by(Inventory.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_warehouse(session: Session, warehouse_id: int) -> list[Inventory]:
        stmt = select(Inventory).where(Inventory.warehouse_id == warehouse_id).order_by(Inventory.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_product(session: Session, product_id: int) -> list[Inventory]:
        stmt = select(Inventory).where(Inventory.product_id == product_id).order_by(Inventory.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_product_and_warehouse(session: Session, product_id: int, warehouse_id: int) -> Inventory | None:
        stmt = select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id
        )
        return session.scalar(stmt)

    @staticmethod
    def update_quantity(row: Inventory, *, stock_quantity: int) -> Inventory:
        row.stock_quantity = stock_quantity
        row.updated_at = datetime.utcnow()
        return row
