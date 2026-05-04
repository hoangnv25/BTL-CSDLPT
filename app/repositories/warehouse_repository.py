from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.warehouse import KhoHang, KhuVucEnum

class KhoHangRepository:
    @staticmethod
    def create(session: Session, *, ten_kho: str, khu_vuc: KhuVucEnum, dia_chi: str) -> KhoHang:
        row = KhoHang(ten_kho=ten_kho, khu_vuc=khu_vuc, dia_chi=dia_chi)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[KhoHang]:
        stmt = select(KhoHang).order_by(KhoHang.ma_kho)
        return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, ma_kho: int) -> KhoHang | None:
        stmt = select(KhoHang).where(KhoHang.ma_kho == ma_kho)
        return session.scalar(stmt)

    @staticmethod
    def update(row: KhoHang, *, ten_kho: str, khu_vuc: KhuVucEnum, dia_chi: str) -> KhoHang:
        row.ten_kho = ten_kho
        row.khu_vuc = khu_vuc
        row.dia_chi = dia_chi
        return row
