from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(tags=["category"])


@router.get(
    "/product_category",
    response_model=list[CategoryOut],
    summary="Liệt kê toàn bộ danh mục sản phẩm",
)
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    return CategoryService(db).list_categories()


@router.post(
    "/product_category",
    response_model=CategoryOut,
    status_code=201,
    summary="Tạo danh mục mới",
)
def create_category(
    body: CategoryCreate, db: Session = Depends(get_db)
) -> CategoryOut:
    return CategoryService(db).create_category(body)


@router.put(
    "/product_category/{ma_danh_muc}",
    response_model=CategoryOut,
    summary="Cập nhật tên danh mục",
)
def update_category(
    ma_danh_muc: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryOut:
    return CategoryService(db).update_category(ma_danh_muc, body)


@router.delete(
    "/product_category/{ma_danh_muc}",
    summary="Xóa danh mục sản phẩm",
)
def delete_category(ma_danh_muc: int, db: Session = Depends(get_db)) -> dict[str, str]:
    return CategoryService(db).delete_category(ma_danh_muc)
