from datetime import datetime
from pydantic import BaseModel
from BE.models.package import PackageStatusEnum
from BE.schemas.user import UserOut
from BE.schemas.warehouse import WarehouseOut
from BE.schemas.order import PackageItemOut


class PackageStatusUpdateRequest(BaseModel):
    status: PackageStatusEnum


class PackageSimpleOut(BaseModel):
    id: int
    order_id: int
    warehouse_id: int
    status: PackageStatusEnum
    delivered_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderForPackageOut(BaseModel):
    id: int
    user: UserOut
    shipping_address: str
    total_amount: float
    ordered_at: datetime
    
    model_config = {"from_attributes": True}


class PackageFullOut(BaseModel):
    id: int
    warehouse: WarehouseOut
    status: PackageStatusEnum
    created_at: datetime
    delivered_at: datetime | None = None
    order: OrderForPackageOut
    items: list[PackageItemOut]

    model_config = {"from_attributes": True}
