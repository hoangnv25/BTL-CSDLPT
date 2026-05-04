from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.inventory_repository import TonKhoRepository
from app.schemas.inventory import InventoryOut, InventoryUpdate

class InventoryService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._inventory_repo = TonKhoRepository()

    def list_inventory(self) -> list[InventoryOut]:
        rows = self._inventory_repo.list_all(self._session)
        return [InventoryOut.model_validate(row) for row in rows]

    def list_by_warehouse(self, ma_kho: int) -> list[InventoryOut]:
        rows = self._inventory_repo.list_by_warehouse(self._session, ma_kho)
        return [InventoryOut.model_validate(row) for row in rows]

    def list_by_product(self, ma_san_pham: int) -> list[InventoryOut]:
        rows = self._inventory_repo.list_by_product(self._session, ma_san_pham)
        return [InventoryOut.model_validate(row) for row in rows]

    def update_inventory(self, body: InventoryUpdate) -> InventoryOut:
        row = self._inventory_repo.find_by_product_and_warehouse(
            self._session, body.ma_san_pham, body.ma_kho
        )
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy bản ghi tồn kho hợp lệ."
            )

        self._inventory_repo.update_quantity(row, so_luong_ton=body.so_luong_ton)
        self._session.commit()
        self._session.refresh(row)
        return InventoryOut.model_validate(row)
