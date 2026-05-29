from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from BE.database import Base

class OrderPackageShard(Base):
    __tablename__ = "order_package_shards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    node_name: Mapped[str] = mapped_column(String(50), nullable=False)  # 'north', 'central', 'south'
