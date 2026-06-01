from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from BE.database import get_db
from BE.services.stats_service import StatsService

router = APIRouter()

@router.get("/top-products", summary="Lấy top sản phẩm bán chạy")
def get_top_products(
    period: str = Query("day", enum=["day", "month", "year"], description="Khoảng thời gian thống kê"),
    specific_date: Optional[date] = Query(None, description="Ngày cụ thể (YYYY-MM-DD)"),
    specific_month: Optional[int] = Query(None, ge=1, le=12, description="Tháng cụ thể (1-12)"),
    specific_year: Optional[int] = Query(None, description="Năm cụ thể (YYYY)"),
    warehouse_id: Optional[int] = Query(None, description="Lọc theo ID kho hàng"),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách top sản phẩm bán chạy.
    Ưu tiên theo specific_date -> (specific_month & specific_year) -> specific_year -> period.
    """
    return StatsService.get_top_products(period, warehouse_id, specific_date, specific_month, specific_year)

@router.get("/revenue", summary="Thống kê doanh thu")
def get_revenue(
    period: str = Query("day", enum=["day", "month", "year"], description="Khoảng thời gian thống kê"),
    specific_date: Optional[date] = Query(None, description="Ngày cụ thể (YYYY-MM-DD)"),
    specific_month: Optional[int] = Query(None, ge=1, le=12, description="Tháng cụ thể (1-12)"),
    specific_year: Optional[int] = Query(None, description="Năm cụ thể (YYYY)"),
    warehouse_id: Optional[int] = Query(None, description="Lọc theo ID kho hàng"),
    db: Session = Depends(get_db)
):
    """
    Trả về báo cáo doanh thu theo thời gian và kho hàng.
    Ưu tiên theo specific_date -> (specific_month & specific_year) -> specific_year -> period.
    """
    return StatsService.get_revenue_stats(period, warehouse_id, specific_date, specific_month, specific_year)
