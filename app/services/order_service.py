from datetime import datetime
from decimal import Decimal
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.package import Package, PackageStatusEnum
from app.models.package_detail import PackageDetail
from app.schemas.order import OrderCreate, OrderOut, PackageOut, PackageItemOut

logger = logging.getLogger("app")

def service_log(service_name: str, content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [{service_name}] {content}"
    print(log_line, flush=True)
    logger.info(log_line)


class OrderService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_order(self, body: OrderCreate) -> OrderOut:
        service_log(
            "OrderService",
            f"Bắt đầu xử lý yêu cầu tạo đơn hàng cho userId = {body.user_id}",
        )

        # 1. Kiểm tra User tồn tại
        user = self._session.query(User).filter(User.id == body.user_id).first()
        if not user:
            service_log("OrderService", f"LỖI: Khách hàng với userId = {body.user_id} không tồn tại trong hệ thống!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khách hàng không tồn tại.",
            )
        service_log(
            "OrderService",
            f"Khách hàng '{user.full_name}' (userId = {user.id}) hợp lệ.",
        )

        # 2. Kiểm tra Sản phẩm tồn tại & Tính tổng tiền tạm tính
        total_amount = Decimal("0.00")
        products_cache = {}
        service_log("OrderService", "Đang kiểm tra tính hợp lệ của danh sách sản phẩm...")
        for item in body.items:
            product = self._session.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                service_log("OrderService", f"LỖI: Sản phẩm với ID = {item.product_id} không tồn tại!")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sản phẩm ID = {item.product_id} không tồn tại.",
                )
            products_cache[item.product_id] = product
            item_total = product.price * item.quantity
            total_amount += item_total
            service_log(
                "OrderService",
                f"Sản phẩm ID = {product.id} ('{product.name}') hợp lệ - Đơn giá: {product.price} - Số lượng yêu cầu: {item.quantity} - Thành tiền: {item_total}",
            )

        service_log("OrderService", f"Tổng tiền đơn hàng tạm tính: {total_amount}")

        # Khởi động Transaction & Khóa dòng tồn kho (with_for_update) chống race conditions
        service_log("OrderService", "Bắt đầu khóa tồn kho toàn cục và thực hiện kiểm tra lượng hàng đáp ứng...")
        
        allocations = {}  # { warehouse_id: [ (product_id, quantity) ] }

        # 3. Kiểm tra Tổng tồn kho & Phân bổ kho hàng
        for item in body.items:
            product = products_cache[item.product_id]
            # Truy vấn tồn kho có khóa bi quan dòng (Pessimistic Lock)
            inventories = (
                self._session.query(Inventory)
                .filter(Inventory.product_id == item.product_id)
                .with_for_update()
                .all()
            )

            total_stock = sum(inv.stock_quantity for inv in inventories)
            service_log(
                "OrderService",
                f"Kiểm tra sản phẩm '{product.name}' (ID={product.id}): Yêu cầu: {item.quantity} | Tổng tồn toàn hệ thống: {total_stock}",
            )

            if total_stock < item.quantity:
                service_log(
                    "OrderService",
                    f"LỖI: Không đủ hàng cho sản phẩm '{product.name}'! Thiếu hụt: {item.quantity - total_stock} sản phẩm.",
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm {product.name} không đủ số lượng tồn kho (Yêu cầu: {item.quantity}, Hiện có: {total_stock}).",
                )
            
            # Sắp xếp kho hàng theo tồn giảm dần (Greedy Allocation)
            inventories_sorted = sorted(inventories, key=lambda x: x.stock_quantity, reverse=True)
            
            remaining = item.quantity
            service_log("OrderService", f"Bắt đầu phân bổ sản phẩm '{product.name}' từ các kho hàng:")
            for inv in inventories_sorted:
                if remaining <= 0:
                    break

                allocated = min(remaining, inv.stock_quantity)
                if allocated > 0:
                    # Trừ tồn kho trong DB
                    old_stock = inv.stock_quantity
                    inv.stock_quantity -= allocated
                    inv.updated_at = datetime.utcnow()
                    
                    service_log(
                        "OrderService",
                        f" -> Chọn Kho ID = {inv.warehouse_id} để cung ứng {allocated} sản phẩm (Tồn cũ: {old_stock} -> Tồn mới: {inv.stock_quantity})",
                    )

                    # Ghi nhận phân bổ
                    if inv.warehouse_id not in allocations:
                        allocations[inv.warehouse_id] = []
                    allocations[inv.warehouse_id].append((item.product_id, allocated))
                    
                    remaining -= allocated

        service_log("OrderService", "Đã phân bổ tồn kho thành công! Khởi tạo các thực thể Đơn hàng và Kiện hàng...")

        # 4. Ghi nhận dữ liệu vào Database
        try:
            # 4.1 Tạo Order
            order = Order(
                user_id=body.user_id,
                shipping_address=body.shipping_address,
                total_amount=total_amount,
                ordered_at=datetime.utcnow(),
            )
            self._session.add(order)
            self._session.flush()
            service_log("OrderService", f"Đã tạo thành công Đơn hàng (Order ID = {order.id}) trong phiên giao dịch.")

            packages_out_list = []

            # 4.2 Tạo các Packages & PackageDetails tương ứng
            for warehouse_id, items_allocated in allocations.items():
                package = Package(
                    order_id=order.id,
                    warehouse_id=warehouse_id,
                    status=PackageStatusEnum.Pending,
                    created_at=datetime.utcnow(),
                )
                self._session.add(package)
                self._session.flush()
                service_log(
                    "OrderService",
                    f" -> Đã tạo Kiện hàng (Package ID = {package.id}) cho nhà kho ID = {warehouse_id}",
                )

                package_items_list = []
                for product_id, qty in items_allocated:
                    detail = PackageDetail(
                        package_id=package.id,
                        product_id=product_id,
                        quantity=qty,
                    )
                    self._session.add(detail)
                    package_items_list.append(
                        PackageItemOut(product_id=product_id, quantity=qty)
                    )
                    service_log(
                        "OrderService",
                        f"     -> Thêm Chi tiết kiện hàng: Sản phẩm ID = {product_id}, Số lượng = {qty}",
                    )

                packages_out_list.append(
                    PackageOut(
                        package_id=package.id,
                        warehouse_id=warehouse_id,
                        status=package.status.value,
                        items=package_items_list,
                    )
                )

            # Commit Transaction
            self._session.commit()
            service_log(
                "OrderService",
                f"Giao dịch hoàn tất thành công! Commit thành công Đơn hàng ID = {order.id}.",
            )

            return OrderOut(
                order_id=order.id,
                user_id=order.user_id,
                shipping_address=order.shipping_address,
                total_amount=order.total_amount,
                ordered_at=order.ordered_at,
                packages=packages_out_list,
            )

        except Exception as e:
            self._session.rollback()
            service_log(
                "OrderService",
                f"LỖI HỆ THỐNG: Có lỗi xảy ra trong quá trình ghi dữ liệu: {str(e)}. Tiến hành Rollback toàn bộ giao dịch!",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi tạo đơn hàng: {str(e)}",
            )
