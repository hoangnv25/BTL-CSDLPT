from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = CategoryRepository()
        self._product_repo = ProductRepository()

    def create_product(self, body: ProductCreate) -> ProductOut:
        self._require_category(body.category_id)

        row = self._product_repo.create(
            self._session,
            name=body.name.strip(),
            category_id=body.category_id,
            price=body.price,
        )
        
        from app.repositories.warehouse_repository import WarehouseRepository
        from app.repositories.inventory_repository import InventoryRepository
        warehouses = WarehouseRepository().list_all(self._session)
        inventory_repo = InventoryRepository()
        for wh in warehouses:
            inventory_repo.create(
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

    def list_products_by_category(self, category_id: int) -> list[ProductOut]:
        self._require_category(category_id)
        rows = self._product_repo.list_by_category(self._session, category_id)
        return [ProductOut.model_validate(row) for row in rows]

    def get_product(self, id: int) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        return ProductOut.model_validate(row)

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
