from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KhachHang


class KhachHangRepository:
    @staticmethod
    def create(session: Session, *, username: str, ho_ten: str) -> KhachHang:
        row = KhachHang(username=username, ho_ten=ho_ten)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def find_by_username(session: Session, username: str) -> KhachHang | None:
        stmt = select(KhachHang).where(KhachHang.username == username)
        return session.scalar(stmt)

    @staticmethod
    def list_all(session: Session) -> list[KhachHang]:
        stmt = select(KhachHang).order_by(KhachHang.ma_khach_hang)
        return list(session.scalars(stmt).all())
