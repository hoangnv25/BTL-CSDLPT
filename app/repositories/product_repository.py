from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import SanPham


class SanPhamRepository:
    @staticmethod
    def create(
        session: Session,
        *,
        ten_san_pham: str,
        ma_danh_muc: int,
        gia_ban: Decimal,
    ) -> SanPham:
        row = SanPham(
            ten_san_pham=ten_san_pham,
            ma_danh_muc=ma_danh_muc,
            gia_ban=gia_ban,
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[SanPham]:
        stmt = select(SanPham).order_by(SanPham.ma_san_pham)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_category(session: Session, ma_danh_muc: int) -> list[SanPham]:
        stmt = (
            select(SanPham)
            .where(SanPham.ma_danh_muc == ma_danh_muc)
            .order_by(SanPham.ma_san_pham)
        )
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, ma_san_pham: int) -> SanPham | None:
        stmt = select(SanPham).where(SanPham.ma_san_pham == ma_san_pham)
        return session.scalar(stmt)

    @staticmethod
    def update(
        row: SanPham,
        *,
        ten_san_pham: str,
        ma_danh_muc: int,
        gia_ban: Decimal,
    ) -> SanPham:
        row.ten_san_pham = ten_san_pham
        row.ma_danh_muc = ma_danh_muc
        row.gia_ban = gia_ban
        return row
