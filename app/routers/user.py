from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLoginRequest, UserLoginResponse, UserOut
from app.services.user_service import UserService

router = APIRouter(tags=["user"])


@router.post("/user", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    return UserService(db).create_user(body)


@router.get("/user", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    return UserService(db).list_users()


@router.post("/user/login", response_model=UserLoginResponse)
def login(body: UserLoginRequest, db: Session = Depends(get_db)) -> UserLoginResponse:
    return UserService(db).login(body.username)
