from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.category_repository import DanhMucSanPhamRepository
from app.repositories.product_repository import SanPhamRepository
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = DanhMucSanPhamRepository()
        self._product_repo = SanPhamRepository()

    def create_product(self, body: ProductCreate) -> ProductOut:
        self._require_category(body.ma_danh_muc)

        row = self._product_repo.create(
            self._session,
            ten_san_pham=body.ten_san_pham.strip(),
            ma_danh_muc=body.ma_danh_muc,
            gia_ban=body.gia_ban,
        )
        self._session.commit()
        self._session.refresh(row)
        return ProductOut.model_validate(row)

    def list_products(self) -> list[ProductOut]:
        rows = self._product_repo.list_all(self._session)
        return [ProductOut.model_validate(row) for row in rows]

    def list_products_by_category(self, ma_danh_muc: int) -> list[ProductOut]:
        self._require_category(ma_danh_muc)
        rows = self._product_repo.list_by_category(self._session, ma_danh_muc)
        return [ProductOut.model_validate(row) for row in rows]

    def get_product(self, ma_san_pham: int) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, ma_san_pham)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )
        return ProductOut.model_validate(row)

    def update_product(self, ma_san_pham: int, body: ProductUpdate) -> ProductOut:
        row = self._product_repo.find_by_id(self._session, ma_san_pham)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy sản phẩm.",
            )

        self._require_category(body.ma_danh_muc)
        self._product_repo.update(
            row,
            ten_san_pham=body.ten_san_pham.strip(),
            ma_danh_muc=body.ma_danh_muc,
            gia_ban=body.gia_ban,
        )
        self._session.commit()
        self._session.refresh(row)
        return ProductOut.model_validate(row)

    def _require_category(self, ma_danh_muc: int) -> None:
        category = self._category_repo.find_by_id(self._session, ma_danh_muc)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )
