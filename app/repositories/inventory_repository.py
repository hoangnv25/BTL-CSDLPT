from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.inventory import TonKho

class TonKhoRepository:
    @staticmethod
    def create(session: Session, *, ma_san_pham: int, ma_kho: int, so_luong_ton: int = 0) -> TonKho:
        row = TonKho(
            ma_san_pham=ma_san_pham,
            ma_kho=ma_kho,
            so_luong_ton=so_luong_ton,
            ngay_cap_nhat=datetime.utcnow()
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[TonKho]:
        stmt = select(TonKho).order_by(TonKho.ma_ton_kho)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_warehouse(session: Session, ma_kho: int) -> list[TonKho]:
        stmt = select(TonKho).where(TonKho.ma_kho == ma_kho).order_by(TonKho.ma_ton_kho)
        return list(session.scalars(stmt).all())

    @staticmethod
    def list_by_product(session: Session, ma_san_pham: int) -> list[TonKho]:
        stmt = select(TonKho).where(TonKho.ma_san_pham == ma_san_pham).order_by(TonKho.ma_ton_kho)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_product_and_warehouse(session: Session, ma_san_pham: int, ma_kho: int) -> TonKho | None:
        stmt = select(TonKho).where(
            TonKho.ma_san_pham == ma_san_pham,
            TonKho.ma_kho == ma_kho
        )
        return session.scalar(stmt)

    @staticmethod
    def update_quantity(row: TonKho, *, so_luong_ton: int) -> TonKho:
        row.so_luong_ton = so_luong_ton
        row.ngay_cap_nhat = datetime.utcnow()
        return row
