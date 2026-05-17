from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithTotalStockOut,
    ProductWithWarehouseStockOut,
    ProductDetailOut,
)
from app.services.product_service import ProductService

router = APIRouter(tags=["product"])

@router.get(
    "/product",
    response_model=list[ProductWithTotalStockOut],
    summary="Liệt kê toàn bộ sản phẩm",
)
def list_products(db: Session = Depends(get_db)) -> list[ProductWithTotalStockOut]:
    return ProductService(db).list_products()

@router.get(
    "/product/by_category",
    response_model=list[ProductWithTotalStockOut],
    summary="Liệt kê sản phẩm theo danh mục",
)
def list_products_by_category(
    category_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[ProductWithTotalStockOut]:
    return ProductService(db).list_products_by_category(category_id)

@router.get(
    "/product/by_warehouse",
    response_model=list[ProductWithWarehouseStockOut],
    summary="Liệt kê sản phẩm có trong một kho",
)
def list_products_by_warehouse(
    warehouse_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[ProductWithWarehouseStockOut]:
    return ProductService(db).list_products_by_warehouse(warehouse_id)

@router.post(
    "/product",
    response_model=ProductOut,
    status_code=201,
    summary="Tạo sản phẩm mới",
)
def create_product(body: ProductCreate, db: Session = Depends(get_db)) -> ProductOut:
    return ProductService(db).create_product(body)

@router.get(
    "/product/{id}",
    response_model=ProductDetailOut,
    summary="Lấy chi tiết một sản phẩm, có cả tồn kho từng kho",
)
def get_product(id: int, db: Session = Depends(get_db)) -> ProductDetailOut:
    return ProductService(db).get_product(id)

@router.put(
    "/product/{id}",
    response_model=ProductOut,
    summary="Cập nhật thông tin sản phẩm",
)
def update_product(
    id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductOut:
    return ProductService(db).update_product(id, body)
