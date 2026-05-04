from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.khach_hang_repository import KhachHangRepository
from app.schemas.user import UserCreate, UserLoginResponse, UserOut


class UserService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = KhachHangRepository()

    def create_user(self, body: UserCreate) -> UserOut:
        try:
            row = self._repo.create(
                self._session, username=body.username.strip(), ho_ten=body.ho_ten.strip()
            )
            self._session.commit()
            self._session.refresh(row)
        except IntegrityError:
            self._session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đăng nhập đã tồn tại.",
            ) from None
        return UserOut.model_validate(row)

    def login(self, username: str) -> UserLoginResponse:
        row = self._repo.find_by_username(self._session, username.strip())
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng.",
            )
        return UserLoginResponse(ma_khach_hang=row.ma_khach_hang, ho_ten=row.ho_ten)

    def list_users(self) -> list[UserOut]:
        rows = self._repo.list_all(self._session)
        return [UserOut.model_validate(r) for r in rows]
