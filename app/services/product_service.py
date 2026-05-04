from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithTotalStockOut,
    ProductWithWarehouseStockOut,
)

class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = CategoryRepository()
        self._product_repo = ProductRepository()
        self._inventory_repo = InventoryRepository()

    def create_product(self, body: ProductCreate) -> ProductOut:
        self._require_category(body.category_id)

        row = self._product_repo.create(
            self._session,
            name=body.name.strip(),
            category_id=body.category_id,
            price=body.price,
        )
        
        from app.repositories.warehouse_repository import WarehouseRepository
        warehouses = WarehouseRepository().list_all(self._session)
        for wh in warehouses:
            self._inventory_repo.create(
                self._session,
                product_id=row.id,
                warehouse_id=wh.id,
                stock_quantity=0
            )
            
        self._session.commit()
        self._session.refresh(row)
        return ProductOut.model_validate(row)

    def list_products(self) -> list[ProductOut]:
        rows = self._product_repo.list_all(self._session)
        return [ProductOut.model_validate(row) for row in rows]

    def list_products_by_category(self, category_id: int) -> list[ProductWithTotalStockOut]:
        self._require_category(category_id)
        rows = self._product_repo.list_by_category(self._session, category_id)
        
        result = []
        for row in rows:
            invs = self._inventory_repo.list_by_product(self._session, row.id)
            total_stock = sum(i.stock_quantity for i in invs)
            result.append(
                ProductWithTotalStockOut(
                    id=row.id,
                    name=row.name,
                    category_id=row.category_id,
                    price=row.price,
                    total_stock=total_stock
                )
            )
        return result

    def list_products_by_warehouse(self, warehouse_id: int) -> list[ProductWithWarehouseStockOut]:
        from app.repositories.warehouse_repository import WarehouseRepository
        wh = WarehouseRepository().find_by_id(self._session, warehouse_id)
        if not wh:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng.",
            )
        
        invs = self._inventory_repo.list_by_warehouse(self._session, warehouse_id)
        result = []
        for inv in invs:
            prod = self._product_repo.find_by_id(self._session, inv.product_id)
            if prod:
                result.append(
                    ProductWithWarehouseStockOut(
                        id=prod.id,
                        name=prod.name,
                        category_id=prod.category_id,
                        price=prod.price,
                        stock_quantity=inv.stock_quantity
                    )
                )
        return result

    def get_product(self, id: int) -> ProductWithTotalStockOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        
        invs = self._inventory_repo.list_by_product(self._session, id)
        total_stock = sum(i.stock_quantity for i in invs)
        return ProductWithTotalStockOut(
            id=row.id,
            name=row.name,
            category_id=row.category_id,
            price=row.price,
            total_stock=total_stock
        )

    def update_product(self, id: int, body: ProductUpdate) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )

        self._require_category(body.category_id)
        self._product_repo.update(
            row,
            name=body.name.strip(),
            category_id=body.category_id,
            price=body.price,
        )
        self._session.commit()
        self._session.refresh(row)
        return ProductOut.model_validate(row)

    def _require_category(self, category_id: int) -> None:
        category = self._category_repo.find_by_id(self._session, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )
