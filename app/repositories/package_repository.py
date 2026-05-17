from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.package import Package, PackageStatusEnum

class PackageRepository:
    @staticmethod
    def create(
        session: Session,
        *,
        order_id: int,
        warehouse_id: int,
        status: PackageStatusEnum = PackageStatusEnum.Pending,
    ) -> Package:
        row = Package(
            order_id=order_id,
            warehouse_id=warehouse_id,
            status=status,
            created_at=datetime.utcnow(),
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def find_by_id(session: Session, id: int) -> Package | None:
        stmt = select(Package).where(Package.id == id)
        return session.scalar(stmt)

    @staticmethod
    def list_by_order(session: Session, order_id: int) -> list[Package]:
        stmt = select(Package).where(Package.order_id == order_id).order_by(Package.id)
        return list(session.scalars(stmt).all())
