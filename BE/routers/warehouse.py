from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from BE.database import get_db
from BE.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate
from BE.services.warehouse_service import WarehouseService

router = APIRouter(tags=["warehouse"])

@router.get(
    "/warehouse",
    response_model=list[WarehouseOut],
    summary="Liệt kê toàn bộ kho hàng",
)
def list_warehouses(db: Session = Depends(get_db)) -> list[WarehouseOut]:
    return WarehouseService(db).list_warehouses()

@router.post(
    "/warehouse",
    response_model=WarehouseOut,
    status_code=201,
    summary="Tạo kho hàng mới",
    description="religon là North, Central hoặc South"
)
def create_warehouse(
    body: WarehouseCreate, db: Session = Depends(get_db)
) -> WarehouseOut:
    return WarehouseService(db).create_warehouse(body)

@router.put(
    "/warehouse/{id}",
    response_model=WarehouseOut,
    summary="Cập nhật thông tin kho hàng",
)
def update_warehouse(
    id: int,
    body: WarehouseUpdate,
    db: Session = Depends(get_db),
) -> WarehouseOut:
    return WarehouseService(db).update_warehouse(id, body)
