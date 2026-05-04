from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TonKho(Base):
    __tablename__ = "TonKho"

    ma_ton_kho: Mapped[int] = mapped_column(
        "MaTonKho", Integer, primary_key=True, autoincrement=True
    )
    ma_san_pham: Mapped[int] = mapped_column(
        "MaSanPham", ForeignKey("SanPham.MaSanPham"), nullable=False
    )
    ma_kho: Mapped[int] = mapped_column(
        "MaKho", ForeignKey("KhoHang.MaKho"), nullable=False
    )
    so_luong_ton: Mapped[int] = mapped_column("SoLuongTon", Integer, nullable=False, default=0)
    ngay_cap_nhat: Mapped[datetime] = mapped_column(
        "NgayCapNhat", DateTime, nullable=False, default=datetime.utcnow
    )
