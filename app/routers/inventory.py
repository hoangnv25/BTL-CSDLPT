from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inventory import InventoryOut, InventoryUpdate
from app.services.inventory_service import InventoryService

router = APIRouter(tags=["inventory"])

@router.get(
    "/inventory",
    response_model=list[InventoryOut],
    summary="Liệt kê toàn bộ tồn kho",
)
def list_inventory(db: Session = Depends(get_db)) -> list[InventoryOut]:
    return InventoryService(db).list_inventory()

@router.get(
    "/inventory/by_warehouse",
    response_model=list[InventoryOut],
    summary="Liệt kê tồn kho theo kho",
)
def list_inventory_by_warehouse(
    warehouse_id: int = Query(...), db: Session = Depends(get_db)
) -> list[InventoryOut]:
    return InventoryService(db).list_by_warehouse(warehouse_id)

@router.get(
    "/inventory/by_product",
    response_model=list[InventoryOut],
    summary="Liệt kê tồn kho theo sản phẩm -- FE bỏ qua",
)
def list_inventory_by_product(
    product_id: int = Query(...), db: Session = Depends(get_db)
) -> list[InventoryOut]:
    return InventoryService(db).list_by_product(product_id)

@router.put(
    "/inventory",
    response_model=InventoryOut,
    summary="Cập nhật số lượng tồn kho",
)
def update_inventory(
    body: InventoryUpdate, db: Session = Depends(get_db)
) -> InventoryOut:
    return InventoryService(db).update_inventory(body)
