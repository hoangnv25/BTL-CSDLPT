from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.order import OrderCreate, OrderOut
from app.services.order_service import OrderService

router = APIRouter(tags=["order"])


@router.post(
    "/order",
    response_model=OrderOut,
    status_code=201,
    summary="""
    Tạo đơn hàng mới và tự động chia kiện hàng theo nhà kho.

    Kho được chọn ưu tiên theo tồn kho lớn nhất của Sản phẩm đó.
    """,
)
def create_order(body: OrderCreate, db: Session = Depends(get_db)) -> OrderOut:
    return OrderService(db).create_order(body)
