from pydantic import BaseModel
from BE.models.package import PackageStatusEnum


class PackageStatusUpdateRequest(BaseModel):
    status: PackageStatusEnum


class PackageSimpleOut(BaseModel):
    id: int
    order_id: int
    warehouse_id: int
    status: PackageStatusEnum

    model_config = {"from_attributes": True}
