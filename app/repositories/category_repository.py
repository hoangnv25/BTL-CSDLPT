from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import DanhMucSanPham


class DanhMucSanPhamRepository:
    @staticmethod
    def create(session: Session, *, ten_danh_muc: str) -> DanhMucSanPham:
        row = DanhMucSanPham(ten_danh_muc=ten_danh_muc)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[DanhMucSanPham]:
        stmt = select(DanhMucSanPham).order_by(DanhMucSanPham.ma_danh_muc)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, ma_danh_muc: int) -> DanhMucSanPham | None:
        stmt = select(DanhMucSanPham).where(DanhMucSanPham.ma_danh_muc == ma_danh_muc)
        return session.scalar(stmt)

    @staticmethod
    def update(row: DanhMucSanPham, *, ten_danh_muc: str) -> DanhMucSanPham:
        row.ten_danh_muc = ten_danh_muc
        return row

    @staticmethod
    def delete(session: Session, row: DanhMucSanPham) -> None:
        session.delete(row)
