from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)

class CategoryUpdate(BaseModel):
    name: str = Field(..., max_length=100)

class CategoryOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
