from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KhachHang(Base):
    __tablename__ = "KhachHang"

    ma_khach_hang: Mapped[int] = mapped_column(
        "MaKhachHang", Integer, primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column("Username", String(100), unique=True, nullable=False)
    ho_ten: Mapped[str] = mapped_column("HoTen", String(255), nullable=False)

