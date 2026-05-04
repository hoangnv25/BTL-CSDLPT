from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    ten_danh_muc: str = Field(..., max_length=100)


class CategoryUpdate(BaseModel):
    ten_danh_muc: str = Field(..., max_length=100)


class CategoryOut(BaseModel):
    ma_danh_muc: int
    ten_danh_muc: str

    model_config = {"from_attributes": True}
