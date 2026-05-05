from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    @staticmethod
    def create(session: Session, *, username: str, full_name: str) -> User:
        row = User(username=username, full_name=full_name)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def find_by_username(session: Session, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return session.scalar(stmt)

    @staticmethod
    def find_all(session: Session) -> list[User]:
        stmt = select(User)
        return session.scalars(stmt).all()
