from datetime import date
from sqlalchemy import Date, Integer, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column
from BE.database import Base

class ProductSalesStat(Base):
    """Thống kê chi tiết theo sản phẩm (Bảng A)"""
    __tablename__ = "product_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    delivered_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", "delivered_at", name="uq_product_warehouse_date"),
    )

class WarehousePerformanceStat(Base):
    """Thống kê tổng quan theo hiệu suất kho (Bảng B)"""
    __tablename__ = "warehouse_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    delivered_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    package_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("warehouse_id", "delivered_at", name="uq_warehouse_performance_date"),
    )

