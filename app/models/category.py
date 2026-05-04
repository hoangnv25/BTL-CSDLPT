from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DanhMucSanPham(Base):
    __tablename__ = "DanhMucSanPham"

    ma_danh_muc: Mapped[int] = mapped_column(
        "MaDanhMuc", Integer, primary_key=True, autoincrement=True
    )
    ten_danh_muc: Mapped[str] = mapped_column("TenDanhMuc", String(100), nullable=False)
