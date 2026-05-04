from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.warehouse import Warehouse, RegionEnum

class WarehouseRepository:
    @staticmethod
    def create(session: Session, *, name: str, region: RegionEnum, address: str) -> Warehouse:
        row = Warehouse(name=name, region=region, address=address)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[Warehouse]:
        stmt = select(Warehouse).order_by(Warehouse.id)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, id: int) -> Warehouse | None:
        stmt = select(Warehouse).where(Warehouse.id == id)
        return session.scalar(stmt)

    @staticmethod
    def update(row: Warehouse, *, name: str, region: RegionEnum, address: str) -> Warehouse:
        row.name = name
        row.region = region
        row.address = address
        return row
