from datetime import datetime
from decimal import Decimal
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from BE.models.user import User
from BE.models.product import Product
from BE.models.inventory import Inventory
from BE.models.order import Order
from BE.models.package import Package, PackageStatusEnum
from BE.models.package_detail import PackageDetail
from BE.schemas.order import OrderCreate, OrderOut, PackageOut, PackageItemOut, OrderListOut
from BE.schemas.user import UserOut

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

        # Chuẩn hóa: Gộp nhóm các sản phẩm trùng lặp và cộng dồn số lượng
        merged_items = {}
        for item in body.items:
            if item.product_id not in merged_items:
                merged_items[item.product_id] = 0
            merged_items[item.product_id] += item.quantity

        from BE.schemas.order import OrderItemCreate
        body.items = [
            OrderItemCreate(product_id=pid, quantity=qty)
            for pid, qty in merged_items.items()
        ]

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
            if product.deleted_at is not None:
                service_log("OrderService", f"LỖI: Sản phẩm với ID = {item.product_id} ('{product.name}') đã bị xóa mềm hoặc ngừng bán!")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm '{product.name}' đã ngừng kinh doanh hoặc bị xóa.",
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
        service_log("OrderService", "Bắt đầu mở các kết nối/transaction đến các Node phụ...")
        
        # 1. Truy vấn các warehouses từ main DB để biết phân vùng miền (Region) của từng warehouse
        from BE.repositories.warehouse_repository import WarehouseRepository
        warehouses_list = WarehouseRepository.list_all(self._session)
        warehouse_regions = {w.id: w.region.value.lower() for w in warehouses_list}
        
        from BE.database import get_db_node, circuit_breaker
        from BE.models.order_package_shard import OrderPackageShard

        # Mở các phiên làm việc (Session) với các Node phụ đang ONLINE
        nodes = ["north", "central", "south"]
        node_sessions = {}
        for node in nodes:
            if circuit_breaker.is_available(node):
                try:
                    sess = get_db_node(node)
                    sess.begin()
                    node_sessions[node] = sess
                    service_log("OrderService", f" -> Khởi động transaction thành công trên Node phụ: [{node}]")
                except Exception as e:
                    circuit_breaker.mark_failure(node)
                    service_log("OrderService", f"CẢNH BÁO: Lỗi mở kết nối đến Node [{node}]: {e}")
            else:
                service_log("OrderService", f" -> Bỏ qua Node [{node}] do Circuit Breaker báo OFFLINE.")

        allocations = {}  # { warehouse_id: { 'node': str, 'items': [ (product_id, quantity) ] } }

        # 3. Kiểm tra Tổng tồn kho & Phân bổ kho hàng
        try:
            for item in body.items:
                product = products_cache[item.product_id]
                
                # Gom các bản ghi tồn kho từ tất cả các Node phụ đang hoạt động
                inventories = []
                for node, sess in node_sessions.items():
                    try:
                        # Khóa dòng bi quan trên Node phụ tương ứng
                        node_invs = sess.query(Inventory).filter(Inventory.product_id == item.product_id).with_for_update().all()
                        inventories.extend(node_invs)
                    except Exception as e:
                        service_log("OrderService", f"CẢNH BÁO: Lỗi đọc inventories từ Node [{node}] cho SP ID={item.product_id}: {e}")
                
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
                        # Trừ tồn kho trên Node phụ tương ứng
                        old_stock = inv.stock_quantity
                        inv.stock_quantity -= allocated
                        inv.updated_at = datetime.utcnow()
                        
                        service_log(
                            "OrderService",
                            f" -> Chọn Kho ID = {inv.warehouse_id} để cung ứng {allocated} sản phẩm (Tồn cũ: {old_stock} -> Tồn mới: {inv.stock_quantity})",
                        )

                        # Ghi nhận phân bổ
                        if inv.warehouse_id not in allocations:
                            allocations[inv.warehouse_id] = {
                                "node": warehouse_regions.get(inv.warehouse_id),
                                "items": []
                            }
                        allocations[inv.warehouse_id]["items"].append((item.product_id, allocated))
                        
                        remaining -= allocated

            service_log("OrderService", "Đã phân bổ tồn kho thành công! Ghi nhận Đơn hàng trên Main DB...")

            # 4. Ghi nhận dữ liệu vào Database
            # 4.1 Tạo Order trên Main DB
            order = Order(
                user_id=body.user_id,
                shipping_address=body.shipping_address,
                total_amount=total_amount,
                ordered_at=datetime.utcnow(),
            )
            self._session.add(order)
            self._session.flush()
            service_log("OrderService", f"Đã chèn và cấp phát Order ID = {order.id} thành công trên Main DB.")

            from BE.models.category import Category
            from BE.schemas.warehouse import WarehouseOut
            from BE.schemas.product import ProductOut

            warehouses = {w.id: WarehouseOut(id=w.id, name=w.name, region=w.region, address=w.address) 
                          for w in warehouses_list if w.id in allocations}
            categories = {c.id: c.name for c in self._session.query(Category).all()}

            packages_out_list = []

            # 4.2 Tạo các Packages & PackageDetails trên các Node phụ tương ứng
            for warehouse_id, alloc_info in allocations.items():
                node_key = alloc_info["node"]
                n_sess = node_sessions.get(node_key)
                if not n_sess:
                    service_log("OrderService", f"LỖI: Node [{node_key}] của kho {warehouse_id} không hoạt động nhưng được phân bổ.")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Lỗi tạo đơn hàng: Node [{node_key}] chứa dữ liệu kho {warehouse_id} đang ngoại tuyến."
                    )
                
                # Tạo Package trên Node phụ
                package = Package(
                    order_id=order.id,
                    warehouse_id=warehouse_id,
                    status=PackageStatusEnum.Pending,
                    created_at=datetime.utcnow(),
                )
                n_sess.add(package)
                n_sess.flush()
                service_log(
                    "OrderService",
                    f" -> Đã tạo Kiện hàng (Package ID = {package.id}) trên Node phụ [{node_key}] cho nhà kho ID = {warehouse_id}",
                )

                # Tạo ánh xạ OrderPackageShard trên Main DB
                mapping = OrderPackageShard(
                    package_id=package.id,
                    order_id=order.id,
                    node_name=node_key
                )
                self._session.add(mapping)
                service_log(
                    "OrderService",
                    f"   -> Lưu ánh xạ kiện hàng ID={package.id} -> Node [{node_key}] trên Main DB."
                )

                package_items_list = []
                for product_id, qty in alloc_info["items"]:
                    detail = PackageDetail(
                        package_id=package.id,
                        product_id=product_id,
                        quantity=qty,
                    )
                    n_sess.add(detail)
                    
                    prod = products_cache[product_id]
                    prod_out = ProductOut(
                        id=prod.id,
                        name=prod.name,
                        category_id=prod.category_id,
                        category_name=categories.get(prod.category_id),
                        price=prod.price
                    )
                    package_items_list.append(
                        PackageItemOut(product=prod_out, quantity=qty)
                    )
                    service_log(
                        "OrderService",
                        f"     -> Thêm Chi tiết kiện hàng trên Node [{node_key}]: Sản phẩm ID = {product_id}, Số lượng = {qty}",
                    )

                packages_out_list.append(
                    PackageOut(
                        package_id=package.id,
                        warehouse=warehouses.get(warehouse_id),
                        status=package.status.value,
                        items=package_items_list,
                    )
                )

            # Commit giao dịch trên Main DB và tất cả các Node phụ liên quan
            self._session.commit()
            service_log("OrderService", "Đã commit thành công đơn hàng và ánh xạ trên Main DB.")
            
            for node, sess in node_sessions.items():
                try:
                    sess.commit()
                    service_log("OrderService", f"Đã commit thành công tồn kho & kiện hàng trên Node phụ [{node}].")
                except Exception as e:
                    service_log("OrderService", f"CẢNH BÁO: Lỗi commit trên Node phụ [{node}]: {e}")
                    raise e

            return OrderOut(
                order_id=order.id,
                user=UserOut(id=user.id, username=user.username, full_name=user.full_name),
                shipping_address=order.shipping_address,
                total_amount=order.total_amount,
                ordered_at=order.ordered_at,
                packages=packages_out_list,
            )

        except Exception as e:
            # Rollback tất cả các session
            self._session.rollback()
            service_log("OrderService", f"Đã rollback giao dịch trên Main DB. Chi tiết lỗi: {e}")
            for node, sess in node_sessions.items():
                try:
                    sess.rollback()
                    service_log("OrderService", f"Đã rollback giao dịch trên Node phụ [{node}].")
                except Exception as roll_err:
                    pass
            raise e
        finally:
            # Đóng tất cả các session node phụ
            for node, sess in node_sessions.items():
                try:
                    sess.close()
                    service_log("OrderService", f"Đã đóng session kết nối đến Node phụ [{node}].")
                except:
                    pass

    def list_orders(self) -> list[OrderListOut]:
        orders = self._session.query(Order).order_by(Order.id.desc()).all()

        # Get all users for the orders in a single query
        user_ids = {order.user_id for order in orders}
        users = self._session.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        users_by_id = {u.id: UserOut(id=u.id, username=u.username, full_name=u.full_name) for u in users}

        result = []
        for order in orders:
            user_out = users_by_id.get(order.user_id)
            if user_out:
                result.append(
                    OrderListOut(
                        order_id=order.id,
                        user=user_out,
                        shipping_address=order.shipping_address,
                        total_amount=order.total_amount,
                        ordered_at=order.ordered_at
                    )
                )
        return result

    def list_my_orders(self, user_id: int) -> list[OrderListOut]:
        orders = self._session.query(Order).filter(Order.user_id == user_id).order_by(Order.id.desc()).all()

        user = self._session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        user_out = UserOut(id=user.id, username=user.username, full_name=user.full_name)

        result = []
        for order in orders:
            result.append(
                OrderListOut(
                    order_id=order.id,
                    user=user_out,
                    shipping_address=order.shipping_address,
                    total_amount=order.total_amount,
                    ordered_at=order.ordered_at
                )
            )
        return result

    def get_order(self, order_id: int) -> OrderOut:
        service_log("OrderService", f"Bắt đầu lấy thông tin chi tiết đơn hàng ID={order_id}")
        order = self._session.query(Order).filter(Order.id == order_id).first()
        if not order:
            service_log("OrderService", f"LỖI: Không tìm thấy đơn hàng ID={order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy đơn hàng.",
            )

        user = self._session.query(User).filter(User.id == order.user_id).first()
        user_out = UserOut(id=user.id, username=user.username, full_name=user.full_name) if user else None

        # 1. Đọc bảng ánh xạ từ Main DB
        from BE.models.order_package_shard import OrderPackageShard
        shard_mappings = self._session.query(OrderPackageShard).filter(OrderPackageShard.order_id == order_id).all()
        target_nodes = list(set(m.node_name for m in shard_mappings))
        service_log("OrderService", f"Ánh xạ chỉ ra các Node chứa kiện hàng của đơn hàng: {target_nodes}")

        packages_data = []
        failed_nodes = []
        is_partial = False
        
        # Nếu chưa có ánh xạ nào (có thể là đơn hàng cũ trước khi sharding), thực hiện quét trên cả 3 Node
        if not target_nodes:
            service_log("OrderService", f"Không tìm thấy ánh xạ. Fallback thực hiện Scatter-Gather trên cả 3 Node phụ...")
            target_nodes = ["north", "central", "south"]

        # 2. Truy vấn kiện hàng từ đúng các Node phụ được chỉ định
        from BE.database import get_db_node, circuit_breaker
        for node in target_nodes:
            if not circuit_breaker.is_available(node):
                service_log("OrderService", f"Circuit Breaker: Bỏ qua Node [{node}] đang ngoại tuyến.")
                is_partial = True
                failed_nodes.append(node)
                continue
            try:
                node_session = get_db_node(node)
                with node_session:
                    node_pkgs = node_session.query(Package).filter(Package.order_id == order_id).all()
                    for p in node_pkgs:
                        # Đọc chi tiết kiện hàng cục bộ
                        details_list = []
                        node_details = node_session.query(PackageDetail).filter(PackageDetail.package_id == p.id).all()
                        for d in node_details:
                            details_list.append({
                                "product_id": d.product_id,
                                "quantity": d.quantity
                            })
                        packages_data.append({
                            "id": p.id,
                            "warehouse_id": p.warehouse_id,
                            "status": p.status,
                            "items": details_list
                        })
                circuit_breaker.mark_success(node)
                service_log("OrderService", f" -> Lấy thành công {len(node_pkgs)} kiện hàng từ Node phụ [{node}]")
            except Exception as e:
                service_log("OrderService", f"CẢNH BÁO: Lỗi đọc kiện hàng trên Node [{node}]: {e}")
                circuit_breaker.mark_failure(node)
                is_partial = True
                failed_nodes.append(node)

        # 3. Lấy thông tin phụ trợ (Warehouses, Products, Categories) từ Main DB
        from BE.repositories.warehouse_repository import WarehouseRepository
        from BE.models.category import Category
        from BE.schemas.warehouse import WarehouseOut
        from BE.schemas.product import ProductOut

        warehouse_ids = {p["warehouse_id"] for p in packages_data}
        warehouses = {w.id: WarehouseOut(id=w.id, name=w.name, region=w.region, address=w.address) 
                      for w in WarehouseRepository.list_by_ids(self._session, list(warehouse_ids))} if warehouse_ids else {}

        product_ids = {item["product_id"] for p in packages_data for item in p["items"]}
        products = self._session.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
        categories = {c.id: c.name for c in self._session.query(Category).all()}
        products_out = {p.id: ProductOut(id=p.id, name=p.name, category_id=p.category_id, category_name=categories.get(p.category_id), price=p.price) 
                        for p in products}

        # 4. Định dạng kết quả trả về
        packages_out_list = []
        for p in packages_data:
            wh_out = warehouses.get(p["warehouse_id"])
            if wh_out:
                package_items_list = []
                for item in p["items"]:
                    prod_out = products_out.get(item["product_id"])
                    if prod_out:
                        package_items_list.append(
                            PackageItemOut(product=prod_out, quantity=item["quantity"])
                        )
                packages_out_list.append(
                    PackageOut(
                        package_id=p["id"],
                        warehouse=wh_out,
                        status=p["status"].value,
                        items=package_items_list
                    )
                )

        warning_msg = None
        if is_partial and failed_nodes:
            region_map = {"north": "Miền Bắc", "central": "Miền Trung", "south": "Miền Nam"}
            friendly_nodes = [region_map.get(n, n) for n in failed_nodes]
            warning_msg = f"Hệ thống tạm thời không thể kết nối tới các Chi nhánh: {', '.join(friendly_nodes)}. Một số thông tin kiện hàng có thể không đầy đủ."

        return OrderOut(
            order_id=order.id,
            user=user_out,
            shipping_address=order.shipping_address,
            total_amount=order.total_amount,
            ordered_at=order.ordered_at,
            packages=packages_out_list,
            is_partial=is_partial,
            warning_message=warning_msg
        )



