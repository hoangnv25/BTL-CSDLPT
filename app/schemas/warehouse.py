from pydantic import BaseModel, Field
from app.models.warehouse import RegionEnum

class WarehouseCreate(BaseModel):
    name: str = Field(..., max_length=100)
    region: RegionEnum
    address: str = Field(..., max_length=255)

class WarehouseUpdate(BaseModel):
    name: str = Field(..., max_length=100)
    region: RegionEnum
    address: str = Field(..., max_length=255)

class WarehouseOut(BaseModel):
    id: int
    name: str
    region: RegionEnum
    address: str

    model_config = {"from_attributes": True}
