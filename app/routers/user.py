from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLoginRequest, UserLoginResponse, UserOut
from app.services.user_service import UserService

router = APIRouter(tags=["user"])

@router.post(
    "/user/register",
    response_model=UserLoginResponse,
    status_code=201,
    summary="Đăng ký tài khoản",
)
def register(body: UserCreate, db: Session = Depends(get_db)) -> UserLoginResponse:
    return UserService(db).register(body)

@router.post(
    "/user/login",
    response_model=UserOut,
    summary="Đăng nhập giả lập",
)
def login(body: UserLoginRequest, db: Session = Depends(get_db)) -> UserLoginResponse:
    return UserService(db).login(body)

@router.get(
    "/users",
    response_model=list[UserOut],
    summary="Lấy danh sách tất cả người dùng",
)
def get_all_users(db: Session = Depends(get_db)) -> list[UserOut]:
    return UserService(db).get_all_users()