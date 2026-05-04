from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import DanhMucSanPhamRepository
from app.repositories.product_repository import SanPhamRepository
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate


class CategoryService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = DanhMucSanPhamRepository()
        self._product_repo = SanPhamRepository()

    def create_category(self, body: CategoryCreate) -> CategoryOut:
        row = self._category_repo.create(self._session, ten_danh_muc=body.ten_danh_muc.strip())
        self._session.commit()
        self._session.refresh(row)
        return CategoryOut.model_validate(row)

    def list_categories(self) -> list[CategoryOut]:
        rows = self._category_repo.list_all(self._session)
        return [CategoryOut.model_validate(row) for row in rows]

    def update_category(self, ma_danh_muc: int, body: CategoryUpdate) -> CategoryOut:
        row = self._category_repo.find_by_id(self._session, ma_danh_muc)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        self._category_repo.update(row, ten_danh_muc=body.ten_danh_muc.strip())
        self._session.commit()
        self._session.refresh(row)
        return CategoryOut.model_validate(row)

    def delete_category(self, ma_danh_muc: int) -> dict[str, str]:
        row = self._category_repo.find_by_id(self._session, ma_danh_muc)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        has_products = self._product_repo.list_by_category(self._session, ma_danh_muc)
        if has_products:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa danh mục vì vẫn còn sản phẩm.",
            )

        self._category_repo.delete(self._session, row)
        self._session.commit()
        return {"message": "Xóa danh mục thành công."}
