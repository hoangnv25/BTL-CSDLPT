from datetime import datetime
from pydantic import BaseModel

class InventoryUpdate(BaseModel):
    id: int
    warehouse_id: int
    stock_quantity: int


class InventoryOut(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    stock_quantity: int
    updated_at: datetime

    model_config = {"from_attributes": True}
