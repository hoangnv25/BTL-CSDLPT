import enum
from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KhuVucEnum(str, enum.Enum):
    Bac = "Bac"
    Trung = "Trung"
    Nam = "Nam"


class KhoHang(Base):
    __tablename__ = "KhoHang"

    ma_kho: Mapped[int] = mapped_column(
        "MaKho", Integer, primary_key=True, autoincrement=True
    )
    ten_kho: Mapped[str] = mapped_column("TenKho", String(100), nullable=False)
    khu_vuc: Mapped[KhuVucEnum] = mapped_column(
        "KhuVuc", Enum(KhuVucEnum, name="khuvuc_enum"), nullable=False
    )
    dia_chi: Mapped[str] = mapped_column("DiaChi", String(255), nullable=False)
