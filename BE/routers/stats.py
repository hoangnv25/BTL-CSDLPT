from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from BE.database import get_db
from BE.services.stats_service import StatsService

from BE.routers.websocket import manager

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

@router.post("/sync", summary="Kích hoạt cập nhật thống kê thủ công")
async def manual_sync_stats(
    specific_date: Optional[date] = Query(None, description="Ngày cụ thể (YYYY-MM-DD)"),
    specific_month: Optional[int] = Query(None, ge=1, le=12, description="Tháng cụ thể (1-12)"),
    specific_year: Optional[int] = Query(None, description="Năm cụ thể (YYYY)")
):
    """
    Kích hoạt tiến trình quét và tổng hợp dữ liệu từ các node nhánh về DB trung tâm ngay lập tức.
    """
    try:
        results = StatsService.sync_all_stats_to_central(
            specific_date=specific_date,
            specific_month=specific_month,
            specific_year=specific_year
        )
        
        # Các thông báo lỗi chi tiết đã được gửi tự động thông qua replication_worker.sync_logs_immediately

        return {"status": "success", "message": "Đã hoàn thành cập nhật thống kê thủ công"}
    except Exception as e:
        print(f"Error in manual_sync_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
