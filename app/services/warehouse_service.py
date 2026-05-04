from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repositories.warehouse_repository import KhoHangRepository
from app.repositories.product_repository import SanPhamRepository
from app.repositories.inventory_repository import TonKhoRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate

class WarehouseService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._warehouse_repo = KhoHangRepository()
        self._product_repo = SanPhamRepository()
        self._inventory_repo = TonKhoRepository()

    def create_warehouse(self, body: WarehouseCreate) -> WarehouseOut:
        row = self._warehouse_repo.create(
            self._session,
            ten_kho=body.ten_kho.strip(),
            khu_vuc=body.khu_vuc,
            dia_chi=body.dia_chi.strip()
        )
        products = self._product_repo.list_all(self._session)
        for product in products:
            self._inventory_repo.create(
                self._session,
                ma_san_pham=product.ma_san_pham,
                ma_kho=row.ma_kho,
                so_luong_ton=0
            )
        
        self._session.commit()
        self._session.refresh(row)
        return WarehouseOut.model_validate(row)

    def list_warehouses(self) -> list[WarehouseOut]:
        rows = self._warehouse_repo.list_all(self._session)
        return [WarehouseOut.model_validate(row) for row in rows]

    def update_warehouse(self, ma_kho: int, body: WarehouseUpdate) -> WarehouseOut:
        row = self._warehouse_repo.find_by_id(self._session, ma_kho)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng."
            )
        
        self._warehouse_repo.update(
            row,
            ten_kho=body.ten_kho.strip(),
            khu_vuc=body.khu_vuc,
            dia_chi=body.dia_chi.strip()
        )
        self._session.commit()
        self._session.refresh(row)
        return WarehouseOut.model_validate(row)
