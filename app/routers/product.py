from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(tags=["product"])


@router.get(
    "/product",
    response_model=list[ProductOut],
    summary="Liệt kê toàn bộ sản phẩm",
)
def list_products(db: Session = Depends(get_db)) -> list[ProductOut]:
    return ProductService(db).list_products()


@router.get(
    "/product/by_category",
    response_model=list[ProductOut],
    summary="Liệt kê sản phẩm theo danh mục",
)
def list_products_by_category(
    ma_danh_muc: int = Query(...),
    db: Session = Depends(get_db),
) -> list[ProductOut]:
    return ProductService(db).list_products_by_category(ma_danh_muc)


@router.post(
    "/product",
    response_model=ProductOut,
    status_code=201,
    summary="Tạo sản phẩm mới",
)
def create_product(body: ProductCreate, db: Session = Depends(get_db)) -> ProductOut:
    return ProductService(db).create_product(body)


@router.get(
    "/product/{ma_san_pham}",
    response_model=ProductOut,
    summary="Lấy chi tiết một sản phẩm",
)
def get_product(ma_san_pham: int, db: Session = Depends(get_db)) -> ProductOut:
    return ProductService(db).get_product(ma_san_pham)


@router.put(
    "/product/{ma_san_pham}",
    response_model=ProductOut,
    summary="Cập nhật thông tin sản phẩm",
)
def update_product(
    ma_san_pham: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductOut:
    return ProductService(db).update_product(ma_san_pham, body)
