from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    ten_san_pham: str = Field(..., max_length=255)
    ma_danh_muc: int
    gia_ban: Decimal = Field(..., decimal_places=2, max_digits=12)


class ProductUpdate(BaseModel):
    ten_san_pham: str = Field(..., max_length=255)
    ma_danh_muc: int
    gia_ban: Decimal = Field(..., decimal_places=2, max_digits=12)


class ProductOut(BaseModel):
    ma_san_pham: int
    ten_san_pham: str
    ma_danh_muc: int
    gia_ban: Decimal

    model_config = {"from_attributes": True}
