import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from BE.database import Base


class PackageStatusEnum(str, enum.Enum):
    Pending = "Pending"
    Shipping = "Shipping"
    Delivered = "Delivered"


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False
    )
    status: Mapped[PackageStatusEnum] = mapped_column(
        Enum(PackageStatusEnum, name="package_status_enum"),
        nullable=False,
        default=PackageStatusEnum.Pending,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
