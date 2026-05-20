from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from BE.repositories.inventory_repository import InventoryRepository
from BE.schemas.inventory import InventoryOut, InventoryUpdate

class InventoryService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._inventory_repo = InventoryRepository()

    def list_inventory(self) -> list[InventoryOut]:
        rows = self._inventory_repo.list_all(self._session)
        return [InventoryOut.model_validate(row) for row in rows]

    def list_by_warehouse(self, warehouse_id: int) -> list[InventoryOut]:
        rows = self._inventory_repo.list_by_warehouse(self._session, warehouse_id)
        return [InventoryOut.model_validate(row) for row in rows]

    def list_by_product(self, product_id: int) -> list[InventoryOut]:
        rows = self._inventory_repo.list_by_product(self._session, product_id)
        return [InventoryOut.model_validate(row) for row in rows]

    def update_inventory(self, body: InventoryUpdate) -> InventoryOut:
        row = self._inventory_repo.find_by_id(self._session, body.id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy bản ghi tồn kho hợp lệ."
            )

        self._inventory_repo.update_quantity(row, stock_quantity=body.stock_quantity)
        self._session.commit()
        self._session.refresh(row)
        return InventoryOut.model_validate(row)

    def get_total_stock_by_product(self, product_id: int) -> int:
        rows = self._inventory_repo.list_by_product(self._session, product_id)
        return sum(row.stock_quantity for row in rows)
