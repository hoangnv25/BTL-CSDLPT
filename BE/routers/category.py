from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from BE.database import get_db, get_read_db
from BE.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from BE.services.category_service import CategoryService

router = APIRouter(tags=["category"])

@router.get(
    "/category",
    response_model=list[CategoryOut],
    summary="Liệt kê toàn bộ danh mục sản phẩm",
)
def list_categories(db: Session = Depends(get_read_db)) -> list[CategoryOut]:
    return CategoryService(db).list_categories()

@router.post(
    "/category",
    response_model=CategoryOut,
    status_code=201,
    summary="Tạo danh mục mới",
)
def create_category(
    body: CategoryCreate, db: Session = Depends(get_db)
) -> CategoryOut:
    return CategoryService(db).create_category(body)

@router.put(
    "/category/{id}",
    response_model=CategoryOut,
    summary="Cập nhật tên danh mục",
)
def update_category(
    id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryOut:
    return CategoryService(db).update_category(id, body)

@router.delete(
    "/category/{id}",
    summary="Xóa danh mục sản phẩm",
)
def delete_category(id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    return CategoryService(db).delete_category(id)
