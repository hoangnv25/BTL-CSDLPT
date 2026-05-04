from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate

class WarehouseService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._warehouse_repo = WarehouseRepository()
        self._product_repo = ProductRepository()
        self._inventory_repo = InventoryRepository()

    def create_warehouse(self, body: WarehouseCreate) -> WarehouseOut:
        row = self._warehouse_repo.create(
            self._session,
            name=body.name.strip(),
            region=body.region,
            address=body.address.strip()
        )
        products = self._product_repo.list_all(self._session)
        for product in products:
            self._inventory_repo.create(
                self._session,
                product_id=product.id,
                warehouse_id=row.id,
                stock_quantity=0
            )
        
        self._session.commit()
        self._session.refresh(row)
        return WarehouseOut.model_validate(row)

    def list_warehouses(self) -> list[WarehouseOut]:
        rows = self._warehouse_repo.list_all(self._session)
        return [WarehouseOut.model_validate(row) for row in rows]

    def update_warehouse(self, id: int, body: WarehouseUpdate) -> WarehouseOut:
        row = self._warehouse_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng."
            )
        
        self._warehouse_repo.update(
            row,
            name=body.name.strip(),
            region=body.region,
            address=body.address.strip()
        )
        self._session.commit()
        self._session.refresh(row)
        return WarehouseOut.model_validate(row)
