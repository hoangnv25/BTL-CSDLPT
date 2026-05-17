from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(..., max_length=255)
    category_id: int
    price: Decimal = Field(..., decimal_places=2, max_digits=12)

class ProductUpdate(BaseModel):
    name: str = Field(..., max_length=255)
    category_id: int
    price: Decimal = Field(..., decimal_places=2, max_digits=12)

class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: str | None = None
    price: Decimal

    model_config = {"from_attributes": True}

class ProductWithTotalStockOut(ProductOut):
    total_stock: int

class ProductWithWarehouseStockOut(ProductOut):
    stock_quantity: int

class ProductInventoryOut(BaseModel):
    id: int
    warehouse_id: int
    warehouse_name: str
    stock_quantity: int
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProductDetailOut(ProductWithTotalStockOut):
    inventory: list[ProductInventoryOut]

