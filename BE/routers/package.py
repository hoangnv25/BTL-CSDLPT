from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from BE.database import get_db
from BE.schemas.package import PackageSimpleOut, PackageStatusUpdateRequest, PackageFullOut
from BE.services.package_service import PackageService

router = APIRouter()

@router.get("/", response_model=list[PackageFullOut], summary="Lấy danh sách kiện hàng")
def list_packages(
    warehouse_id: Optional[int] = Query(None, description="Lọc kiện hàng theo ID kho"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách kiện hàng. 
    Nếu có `warehouse_id`, trả về các kiện hàng thuộc kho đó.
    Nếu không có, trả về tất cả.
    Thông tin trả về bao gồm chi tiết kiện, thông tin sản phẩm, thông tin khách hàng và đơn hàng.
    """
    return PackageService.list_packages(db, warehouse_id)

@router.put("/{package_id}/status", response_model=PackageSimpleOut, summary="Cập nhật trạng thái kiện hàng")
def update_package_status(
    package_id: int,
    request: PackageStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Cập nhật trạng thái kiện hàng dựa vào package_id.
    
    Có 3 trạng thái enum là  "Pending", "Shipping" và "Delivered" 
    """
    return PackageService.update_package_status(db, package_id, request)
