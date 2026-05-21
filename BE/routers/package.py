from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from BE.database import get_db
from BE.schemas.package import PackageSimpleOut, PackageStatusUpdateRequest
from BE.services.package_service import PackageService

router = APIRouter()

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
