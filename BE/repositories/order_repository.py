from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from BE.models.order import Order

class OrderRepository:
    @staticmethod
    def create(
        session: Session,
        *,
        user_id: int,
        shipping_address: str,
        total_amount: Decimal,
    ) -> Order:
        row = Order(
            user_id=user_id,
            shipping_address=shipping_address,
            total_amount=total_amount,
            ordered_at=datetime.utcnow(),
        )
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def find_by_id(session: Session, id: int) -> Order | None:
        stmt = select(Order).where(Order.id == id)
        return session.scalar(stmt)

    @staticmethod
    def list_by_user(session: Session, user_id: int) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.ordered_at.desc())
        return list(session.scalars(stmt).all())
