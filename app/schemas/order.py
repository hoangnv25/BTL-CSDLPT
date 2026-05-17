from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    user_id: int
    shipping_address: str = Field(..., max_length=255)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class PackageItemOut(BaseModel):
    product_id: int
    quantity: int

    model_config = {"from_attributes": True}


class PackageOut(BaseModel):
    package_id: int
    warehouse_id: int
    status: str
    items: list[PackageItemOut]

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    order_id: int
    user_id: int
    shipping_address: str
    total_amount: Decimal
    ordered_at: datetime
    packages: list[PackageOut]

    model_config = {"from_attributes": True}
