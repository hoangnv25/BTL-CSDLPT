from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.package_detail import PackageDetail

class PackageDetailRepository:
    @staticmethod
    def create(
        session: Session,
        *,
        package_id: int,
        product_id: int,
        quantity: int,
    ) -> PackageDetail:
        row = PackageDetail(
            package_id=package_id,
            product_id=product_id,
            quantity=quantity,
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_by_package(session: Session, package_id: int) -> list[PackageDetail]:
        stmt = select(PackageDetail).where(PackageDetail.package_id == package_id).order_by(PackageDetail.id)
        return list(session.scalars(stmt).all())
