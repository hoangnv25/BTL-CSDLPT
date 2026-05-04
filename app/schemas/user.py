from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., max_length=100)
    full_name: str = Field(..., max_length=255)

class UserLoginRequest(BaseModel):
    username: str = Field(..., max_length=100)

class UserLoginResponse(BaseModel):
    id: int
    full_name: str

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str

    model_config = {"from_attributes": True}
