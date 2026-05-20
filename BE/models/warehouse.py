import enum
from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from BE.database import Base


class RegionEnum(str, enum.Enum):
    North = "North"
    Central = "Central"
    South = "South"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[RegionEnum] = mapped_column(
        Enum(RegionEnum, name="region_enum"), nullable=False
    )
    address: Mapped[str] = mapped_column(String(255), nullable=False)
