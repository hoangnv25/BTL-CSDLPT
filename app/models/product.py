from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SanPham(Base):
    __tablename__ = "SanPham"

    ma_san_pham: Mapped[int] = mapped_column(
        "MaSanPham", Integer, primary_key=True, autoincrement=True
    )
    ten_san_pham: Mapped[str] = mapped_column("TenSanPham", String(255), nullable=False)
    ma_danh_muc: Mapped[int] = mapped_column(
        "MaDanhMuc", ForeignKey("DanhMucSanPham.MaDanhMuc"), nullable=False
    )
    gia_ban: Mapped[Decimal] = mapped_column("GiaBan", Numeric(12, 2), nullable=False)
