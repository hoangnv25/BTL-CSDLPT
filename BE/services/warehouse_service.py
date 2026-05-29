from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from BE.repositories.warehouse_repository import WarehouseRepository
from BE.repositories.product_repository import ProductRepository
from BE.repositories.inventory_repository import InventoryRepository
from BE.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate

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
        service_log("WarehouseService", f"Bắt đầu tạo kho hàng mới '{body.name}' tại vùng {body.region}")
        
        row = self._warehouse_repo.create(
            self._session,
            name=body.name.strip(),
            region=body.region,
            address=body.address.strip()
        )
        self._session.flush() # ensure warehouse id is generated
        
        # Xác định DB node phụ từ vùng miền của kho hàng
        node_key = body.region.value.lower() # "north", "central", "south"
        service_log(
            "WarehouseService", 
            f"Định tuyến khởi tạo tồn kho phân mảnh cho kho '{row.name}' (ID={row.id}) -> Node phụ: [{node_key}]"
        )
        
        # Lấy toàn bộ sản phẩm (kể cả sản phẩm bị xóa mềm) để khởi tạo tồn kho
        products = self._product_repo.list_all(self._session, include_deleted=True)
        
        # Mở session trên Node phụ và tạo tồn kho mặc định
        node_session = get_db_node(node_key)
        try:
            for product in products:
                service_log(
                    "WarehouseService",
                    f"Chèn dòng tồn kho mặc định (quantity=0) cho sản phẩm {product.name} (ID={product.id}) trên Node: [{node_key}]"
                )
                self._inventory_repo.create(
                    node_session,
                    product_id=product.id,
                    warehouse_id=row.id,
                    stock_quantity=0
                )
            node_session.commit()
            service_log("WarehouseService", f"Lưu thành công dữ liệu tồn kho phân sharding trên Node phụ [{node_key}].")
        except Exception as e:
            node_session.rollback()
            service_log("WarehouseService", f"LỖI khi khởi tạo tồn kho trên Node phụ [{node_key}]: {e}")
            raise e
        finally:
            node_session.close()
        
        self._session.commit()
        self._session.refresh(row)
        service_log("WarehouseService", f"Hoàn tất tạo kho hàng mới '{row.name}' (ID={row.id}) trên main DB.")
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
