from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., max_length=100)
    ho_ten: str = Field(..., max_length=255)


class UserLoginRequest(BaseModel):
    username: str = Field(..., max_length=100)


class UserLoginResponse(BaseModel):
    ma_khach_hang: int
    ho_ten: str


class UserOut(BaseModel):
    ma_khach_hang: int
    username: str
    ho_ten: str

    model_config = {"from_attributes": True}
