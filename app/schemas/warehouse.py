from pydantic import BaseModel, Field
from app.models.warehouse import KhuVucEnum

class WarehouseCreate(BaseModel):
    ten_kho: str = Field(..., max_length=100)
    khu_vuc: KhuVucEnum
    dia_chi: str = Field(..., max_length=255)

class WarehouseUpdate(BaseModel):
    ten_kho: str = Field(..., max_length=100)
    khu_vuc: KhuVucEnum
    dia_chi: str = Field(..., max_length=255)

class WarehouseOut(BaseModel):
    ma_kho: int
    ten_kho: str
    khu_vuc: KhuVucEnum
    dia_chi: str

    model_config = {"from_attributes": True}
