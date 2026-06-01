from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from BE.repositories.warehouse_repository import WarehouseRepository
from BE.repositories.product_repository import ProductRepository
from BE.repositories.inventory_repository import InventoryRepository
from BE.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate
from BE.models.warehouse import Warehouse

import logging
from datetime import datetime
from BE.database import get_db_node

logger = logging.getLogger("app")

def service_log(service_name: str, content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [{service_name}] {content}"
    print(log_line, flush=True)
    logger.info(log_line)


class WarehouseService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._warehouse_repo = WarehouseRepository()
        self._product_repo = ProductRepository()
        self._inventory_repo = InventoryRepository()

    def create_warehouse(self, body: WarehouseCreate) -> WarehouseOut:
        node_key = body.region.value.lower() # "north", "central", "south"
        service_log("WarehouseService", f"Bắt đầu tạo kho hàng mới '{body.name}' tại Node phụ: [{node_key}]")
        
        node_session = get_db_node(node_key)
        try:
            # 1. Tạo kho hàng cục bộ trên Node phụ đích
            row = self._warehouse_repo.create(
                node_session,
                name=body.name.strip(),
                region=body.region,
                address=body.address.strip()
            )
            node_session.flush()
            
            # 2. Tạo sẵn các dòng tồn kho với số lượng = 0 trên Node phụ đích đó
            products = self._product_repo.list_all(self._session, include_deleted=True)
            for product in products:
                self._inventory_repo.create(
                    node_session,
                    product_id=product.id,
                    warehouse_id=row.id,
                    stock_quantity=0
                )
            
            node_session.commit()
            
            # Đảm bảo các thuộc tính được tải đầy đủ trước khi expunge
            node_session.refresh(row)
            out_data = WarehouseOut.model_validate(row)
            
            node_session.expunge(row)
            service_log("WarehouseService", f"Hoàn tất tạo kho hàng '{row.name}' (ID={row.id}) trên Node phụ [{node_key}].")
            return out_data
        except Exception as e:
            node_session.rollback()
            raise e
        finally:
            node_session.close()

    def list_warehouses(self) -> list[WarehouseOut]:
        rows = self._warehouse_repo.list_all(self._session)
        return [WarehouseOut.model_validate(row) for row in rows]

    def update_warehouse(self, id: int, body: WarehouseUpdate) -> WarehouseOut:
        # 1. Tìm thông tin kho hiện tại
        current_wh = self._warehouse_repo.find_by_id(self._session, id)
        if current_wh is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng."
            )
        
        # 2. Ràng buộc toàn vẹn phân mảnh: Cấm đổi region
        if current_wh.region != body.region:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể thay đổi vùng miền (region) của kho hàng do ràng buộc phân mảnh vật lý. Vui lòng tạo kho mới nếu cần thiết."
            )
            
        # 3. Định tuyến cập nhật đến đúng Node chứa kho hàng
        node_key = current_wh.region.value.lower()
        node_session = get_db_node(node_key)
        try:
            row = node_session.query(Warehouse).filter(Warehouse.id == id).first()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kho trên Node phụ.")
                
            self._warehouse_repo.update(
                row,
                name=body.name.strip(),
                region=body.region,
                address=body.address.strip()
            )
            node_session.commit()
            
            node_session.refresh(row)
            out_data = WarehouseOut.model_validate(row)
            node_session.expunge(row)
            return out_data
        except Exception as e:
            node_session.rollback()
            raise e
        finally:
            node_session.close()
