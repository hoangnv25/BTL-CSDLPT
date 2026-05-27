from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json

from BE.repositories.category_repository import CategoryRepository
from BE.repositories.product_repository import ProductRepository
from BE.repositories.inventory_repository import InventoryRepository
from BE.models.replication_log import ReplicationLog
from BE.workers.replication_worker import replication_worker
from BE.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithTotalStockOut,
    ProductWithWarehouseStockOut,
    ProductDetailOut,
    ProductInventoryOut,
)

class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = CategoryRepository()
        self._product_repo = ProductRepository()
        self._inventory_repo = InventoryRepository()
        self._nodes = ["north", "central", "south"]

    def _add_replication_logs(self, action: str, record_id: int, data_payload: str | None = None) -> list[int]:
        log_ids = []
        for node in self._nodes:
            log = ReplicationLog(
                table_name="product",
                record_id=record_id,
                action=action,
                data_payload=data_payload,
                target_node=node,
                status="PENDING"
            )
            self._session.add(log)
            log_ids.append(-1) # Placeholder since we don't need real IDs anymore
        return log_ids

    def create_product(self, body: ProductCreate) -> ProductOut:
        category = self._category_repo.find_by_id(self._session, body.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        row = self._product_repo.create(
            self._session,
            name=body.name.strip(),
            category_id=body.category_id,
            price=body.price,
        )
        
        from BE.repositories.warehouse_repository import WarehouseRepository
        warehouses = WarehouseRepository().list_all(self._session)
        for wh in warehouses:
            self._inventory_repo.create(
                self._session,
                product_id=row.id,
                warehouse_id=wh.id,
                stock_quantity=0
            )
            
        self._session.flush() # ensure id is generated
        
        log_ids = self._add_replication_logs(
            action="INSERT", 
            record_id=row.id, 
            data_payload=json.dumps({
                "name": row.name,
                "category_id": row.category_id,
                "price": float(row.price)
            })
        )
        
        self._session.commit()
        replication_worker.trigger()
        # self._session.refresh(row)
        
        out = ProductOut.model_validate(row)
        out.category_name = category.name
        return out

    def list_products(self, include_deleted: bool = False) -> list[ProductWithTotalStockOut]:
        from BE.services.inventory_service import InventoryService
        inv_service = InventoryService(self._session)
        
        rows = self._product_repo.list_all(self._session, include_deleted=include_deleted)
        categories = {c.id: c.name for c in self._category_repo.list_all(self._session)}
        
        result = []
        for row in rows:
            total_stock = inv_service.get_total_stock_by_product(row.id)
            result.append(
                ProductWithTotalStockOut(
                    id=row.id,
                    name=row.name,
                    category_id=row.category_id,
                    category_name=categories.get(row.category_id),
                    price=row.price,
                    total_stock=total_stock,
                    deleted_at=row.deleted_at
                )
            )
        return result

    def list_products_by_category(self, category_id: int, include_deleted: bool = False) -> list[ProductWithTotalStockOut]:
        category = self._category_repo.find_by_id(self._session, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )
        rows = self._product_repo.list_by_category(self._session, category_id, include_deleted=include_deleted)
        
        result = []
        for row in rows:
            invs = self._inventory_repo.list_by_product(self._session, row.id)
            total_stock = sum(i.stock_quantity for i in invs)
            result.append(
                ProductWithTotalStockOut(
                    id=row.id,
                    name=row.name,
                    category_id=row.category_id,
                    category_name=category.name,
                    price=row.price,
                    total_stock=total_stock,
                    deleted_at=row.deleted_at
                )
            )
        return result

    def list_products_by_warehouse(self, warehouse_id: int, include_deleted: bool = False) -> list[ProductWithWarehouseStockOut]:
        from BE.repositories.warehouse_repository import WarehouseRepository
        wh = WarehouseRepository().find_by_id(self._session, warehouse_id)
        if not wh:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng.",
            )
        
        categories = {c.id: c.name for c in self._category_repo.list_all(self._session)}
        invs = self._inventory_repo.list_by_warehouse(self._session, warehouse_id)
        result = []
        for inv in invs:
            prod = self._product_repo.find_by_id(self._session, inv.product_id)
            if prod and (include_deleted or prod.deleted_at is None):
                result.append(
                    ProductWithWarehouseStockOut(
                        id=prod.id,
                        name=prod.name,
                        category_id=prod.category_id,
                        category_name=categories.get(prod.category_id),
                        price=prod.price,
                        stock_quantity=inv.stock_quantity,
                        deleted_at=prod.deleted_at
                    )
                )
        return result

    def get_product(self, id: int) -> ProductDetailOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        
        category = self._category_repo.find_by_id(self._session, row.category_id)
        category_name = category.name if category else None
        
        invs = self._inventory_repo.list_by_product(self._session, id)
        total_stock = sum(i.stock_quantity for i in invs)

        from BE.repositories.warehouse_repository import WarehouseRepository
        warehouses = {w.id: w.name for w in WarehouseRepository.list_all(self._session)}

        inventory_list = []
        for inv in invs:
            inventory_list.append(
                ProductInventoryOut(
                    id=inv.id,
                    warehouse_id=inv.warehouse_id,
                    warehouse_name=warehouses.get(inv.warehouse_id, "Unknown"),
                    stock_quantity=inv.stock_quantity,
                    updated_at=inv.updated_at
                )
            )

        return ProductDetailOut(
            id=row.id,
            name=row.name,
            category_id=row.category_id,
            category_name=category_name,
            price=row.price,
            total_stock=total_stock,
            inventory=inventory_list,
            deleted_at=row.deleted_at
        )

    def update_product(self, id: int, body: ProductUpdate) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )

        category = self._category_repo.find_by_id(self._session, body.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        self._product_repo.update(
            row,
            name=body.name.strip(),
            category_id=body.category_id,
            price=body.price,
        )
        
        self._add_replication_logs(
            action="UPDATE", 
            record_id=row.id, 
            data_payload=json.dumps({
                "name": row.name,
                "category_id": row.category_id,
                "price": float(row.price)
            })
        )
        
        self._session.commit()
        replication_worker.trigger()
        # self._session.refresh(row)
        
        out = ProductOut.model_validate(row)
        out.category_name = category.name
        return out

    def soft_delete_product(self, id: int) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        category = self._category_repo.find_by_id(self._session, row.category_id)
        category_name = category.name if category else None

        self._product_repo.delete(self._session, row)
        
        log_ids = self._add_replication_logs(
            action="DELETE", 
            record_id=row.id
        )
        
        self._session.commit()
        replication_worker.trigger()
        # self._session.refresh(row)
        
        out = ProductOut.model_validate(row)
        out.category_name = category_name
        return out

    def restore_product(self, id: int) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        category = self._category_repo.find_by_id(self._session, row.category_id)
        category_name = category.name if category else None

        self._product_repo.restore(self._session, row)
        
        log_ids = self._add_replication_logs(
            action="RESTORE", 
            record_id=row.id
        )
        
        self._session.commit()
        replication_worker.trigger()
        # self._session.refresh(row)  <-- Bỏ refresh nếu không thực sự cần dữ liệu mới nhất ngay lập tức
        
        out = ProductOut.model_validate(row)
        out.category_name = category_name
        return out

    def _require_category(self, category_id: int) -> None:
        category = self._category_repo.find_by_id(self._session, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )
