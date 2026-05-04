from datetime import datetime
from pydantic import BaseModel

class InventoryUpdate(BaseModel):
    ma_kho: int
    ma_san_pham: int
    so_luong_ton: int

class InventoryOut(BaseModel):
    ma_ton_kho: int
    ma_san_pham: int
    ma_kho: int
    so_luong_ton: int
    ngay_cap_nhat: datetime

    model_config = {"from_attributes": True}
