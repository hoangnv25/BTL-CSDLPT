from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from BE.database import Base

class ReplicationLog(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # Các hành động: INSERT, UPDATE, DELETE, SYNC_STATS
    data_payload: Mapped[str | None] = mapped_column(Text, nullable=True) # Nội dung dữ liệu định dạng JSON
    target_node: Mapped[str] = mapped_column(String(50), nullable=False) # Node đích: north, central, south
    status: Mapped[str] = mapped_column(String(20), default="PENDING") # Trạng thái: PENDING, SUCCESS, FAILED
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    next_retry_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

