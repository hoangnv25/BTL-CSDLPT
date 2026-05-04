from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLoginRequest, UserLoginResponse

class UserService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._user_repo = UserRepository()

    def register(self, body: UserCreate) -> UserLoginResponse:
        row = self._user_repo.find_by_username(self._session, body.username.strip())
        if row:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập đã tồn tại.",
            )
        
        row = self._user_repo.create(
            self._session,
            username=body.username.strip(),
            full_name=body.full_name.strip(),
        )
        self._session.commit()
        self._session.refresh(row)
        return UserLoginResponse.model_validate(row)

    def login(self, body: UserLoginRequest) -> UserLoginResponse:
        row = self._user_repo.find_by_username(self._session, body.username.strip())
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng.",
            )
        return UserLoginResponse.model_validate(row)
