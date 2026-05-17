from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.order import OrderCreate, OrderOut, OrderListOut
from app.services.order_service import OrderService

router = APIRouter(tags=["order"])


@router.post(
    "/order",
    response_model=OrderOut,
    status_code=201,
    summary="Tạo đơn hàng",
    description="""
    Tạo đơn hàng mới và tự động chia kiện hàng theo nhà kho.
    
    Nhà kho được chọn ưu tiên dựa trên số lượng tồn kho lớn nhất của sản phẩm đó.
    """,
)
def create_order(body: OrderCreate, db: Session = Depends(get_db)) -> OrderOut:
    return OrderService(db).create_order(body)


@router.get(
    "/order",
    response_model=list[OrderListOut],
    summary="Xem danh sách toàn bộ đơn hàng trong hệ thống",
    description="Lấy danh sách tóm tắt của tất cả các đơn hàng (không bao gồm thông tin chi tiết các kiện hàng và sản phẩm).",
)
def list_orders(db: Session = Depends(get_db)) -> list[OrderListOut]:
    return OrderService(db).list_orders()


@router.get(
    "/order/{id}",
    response_model=OrderOut,
    summary="Xem chi tiết một đơn hàng",
    description="Lấy thông tin chi tiết của một đơn hàng cụ thể kèm theo toàn bộ thông tin kiện hàng và sản phẩm.",
)
def get_order(id: int, db: Session = Depends(get_db)) -> OrderOut:
    return OrderService(db).get_order(id)


