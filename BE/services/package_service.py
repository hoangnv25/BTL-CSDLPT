import logging
from datetime import datetime
from concurrent.futures import wait
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from BE.database import get_db_node, circuit_breaker
from BE.services.inventory_service import inventory_thread_pool
from BE.models.package import Package, PackageStatusEnum
from BE.models.package_detail import PackageDetail
from BE.models.order_package_shard import OrderPackageShard
from BE.schemas.package import PackageSimpleOut, PackageStatusUpdateRequest, PackageFullOut, OrderForPackageOut

logger = logging.getLogger("app")

def package_service_log(content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [PackageService] {content}"
    print(log_line, flush=True)
    logger.info(log_line)


class PackageService:
    @staticmethod
    def update_package_status(
        session: Session, package_id: int, request: PackageStatusUpdateRequest
    ) -> PackageSimpleOut:
        package_service_log(f"Bắt đầu yêu cầu cập nhật trạng thái kiện hàng ID={package_id} sang '{request.status.value}'")
        
        # 1. Tìm Node chứa package_id thông qua bảng ánh xạ trên Main DB
        mapping = session.query(OrderPackageShard).filter(OrderPackageShard.package_id == package_id).first()
        target_node = mapping.node_name if mapping else None
        
        # 2. Fallback nếu không có ánh xạ (đơn hàng cũ), quét song song trên 3 Node
        if not target_node:
            package_service_log(f"Không tìm thấy ánh xạ cho package_id={package_id} trên Main DB. Đang thực hiện tìm kiếm song song...")
            
            def check_node(node: str) -> str | None:
                if not circuit_breaker.is_available(node):
                    return None
                try:
                    node_session = get_db_node(node)
                    with node_session:
                        exists = node_session.query(Package).filter(Package.id == package_id).first()
                        circuit_breaker.mark_success(node)
                        if exists:
                            return node
                except Exception as e:
                    circuit_breaker.mark_failure(node)
                    package_service_log(f"CẢNH BÁO: Lỗi kết nối Node [{node}] khi quét package_id: {e}")
                return None

            futures = {inventory_thread_pool.submit(check_node, node): node for node in ["north", "central", "south"]}
            done, not_done = wait(futures.keys(), timeout=0.5)
            for f in done:
                res = f.result()
                if res:
                    target_node = res
                    break

        if not target_node:
            package_service_log(f"LỖI: Không tìm thấy kiện hàng ID={package_id} trên bất kỳ Node phụ nào!")
            raise HTTPException(status_code=404, detail="Không tìm thấy kiện hàng")

        package_service_log(f"Định tuyến yêu cầu cập nhật đến Node phụ: [{target_node}]")
        
        if not circuit_breaker.is_available(target_node):
            package_service_log(f"LỖI: Node phụ [{target_node}] đang ngoại tuyến.")
            raise HTTPException(status_code=500, detail=f"Không thể kết nối đến Node [{target_node}] (Circuit Breaker).")

        node_session = get_db_node(target_node)
        try:
            row = node_session.query(Package).filter(Package.id == package_id).with_for_update().first()
            if not row:
                raise HTTPException(status_code=404, detail="Không tìm thấy kiện hàng trên Node phụ")
                
            old_status = row.status
            new_status = request.status
            row.status = new_status
            
            # Nếu trạng thái chuyển sang Delivered, việc tổng hợp báo cáo sẽ được thực hiện định kỳ ở DB trung tâm
            if new_status == PackageStatusEnum.Delivered and old_status != PackageStatusEnum.Delivered:
                package_service_log(f"Kiện hàng ID={package_id} đã được giao. Dữ liệu sẽ được tổng hợp về DB tập trung định kỳ.")

            node_session.commit()
            
            package_service_log(f"Cập nhật trạng thái thành công trên Node [{target_node}]: {old_status} -> {request.status.value}")
            return PackageSimpleOut(
                id=row.id,
                order_id=row.order_id,
                warehouse_id=row.warehouse_id,
                status=row.status
            )
        except Exception as e:
            node_session.rollback()
            package_service_log(f"LỖI khi cập nhật trạng thái kiện hàng trên Node [{target_node}]: {e}")
            raise e
        finally:
            node_session.close()

    @staticmethod
    def list_packages(session: Session, warehouse_id: int | None = None) -> list[PackageFullOut]:
        package_service_log(f"Bắt đầu lấy danh sách kiện hàng (warehouse_id={warehouse_id})")
        
        # 1. Xác định các Node phụ cần truy vấn
        target_nodes = []
        if warehouse_id is not None:
            from BE.repositories.warehouse_repository import WarehouseRepository
            wh = WarehouseRepository.find_by_id(session, warehouse_id)
            if not wh:
                package_service_log(f"LỖI: Không tìm thấy kho hàng ID={warehouse_id}")
                raise HTTPException(status_code=404, detail="Không tìm thấy kho hàng")
            target_nodes = [wh.region.value.lower()]
            package_service_log(f"Lọc theo kho ID={warehouse_id} -> Định tuyến đến đúng Node: {target_nodes}")
        else:
            target_nodes = ["north", "central", "south"]
            package_service_log(f"Lấy tất cả kiện hàng -> Scatter-Gather truy vấn song song cả 3 Node phụ: {target_nodes}")

        # 2. Truy vấn song song dữ liệu Packages & PackageDetails từ các Node
        def query_packages_on_node(node: str) -> list:
            if not circuit_breaker.is_available(node):
                package_service_log(f"Circuit Breaker: Bỏ qua kết nối đến Node [{node}] do đang ở trạng thái OFFLINE.")
                return []
            try:
                node_session = get_db_node(node)
                with node_session:
                    query = node_session.query(Package)
                    if warehouse_id is not None:
                        query = query.filter(Package.warehouse_id == warehouse_id)
                    packages = query.all()
                    
                    # Tối ưu: Lấy toàn bộ chi tiết kiện hàng trong một lần query (tránh N+1)
                    package_ids = [p.id for p in packages]
                    all_details = []
                    if package_ids:
                        all_details = node_session.query(PackageDetail).filter(PackageDetail.package_id.in_(package_ids)).all()
                    
                    details_map = {}
                    for d in all_details:
                        details_map.setdefault(d.package_id, []).append({
                            "id": d.id,
                            "package_id": d.package_id,
                            "product_id": d.product_id,
                            "quantity": d.quantity
                        })

                    result_list = []
                    for p in packages:
                        result_list.append({
                            "id": p.id,
                            "order_id": p.order_id,
                            "warehouse_id": p.warehouse_id,
                            "status": p.status,
                            "created_at": p.created_at,
                            "details": details_map.get(p.id, [])
                        })
                    circuit_breaker.mark_success(node)
                    return result_list
            except Exception as e:
                circuit_breaker.mark_failure(node)
                package_service_log(f"CẢNH BÁO: Lỗi đọc kiện hàng trên Node phụ [{node}]: {e}")
                return []

        combined_packages = []
        futures = {inventory_thread_pool.submit(query_packages_on_node, node): node for node in target_nodes}
        # Tăng timeout lên 2.0s để đảm bảo các truy vấn phức tạp kịp hoàn tất
        done, not_done = wait(futures.keys(), timeout=2.0)

        for f in done:
            node = futures[f]
            results = f.result()
            package_service_log(f" -> Lấy thành công {len(results)} kiện hàng từ Node phụ: [{node}]")
            combined_packages.extend(results)

        for f in not_done:
            node = futures[f]
            circuit_breaker.mark_failure(node)
            package_service_log(f"TIMEOUT: Node [{node}] không phản hồi trong 0.5s. Bỏ qua và đánh dấu OFFLINE.")

        if not combined_packages:
            return []

        combined_packages.sort(key=lambda x: x["id"], reverse=True)

        # 3. Lấy thông tin chi tiết từ Main DB
        from BE.models.order import Order
        from BE.models.user import User
        from BE.repositories.warehouse_repository import WarehouseRepository
        from BE.models.product import Product
        from BE.models.category import Category
        from BE.schemas.warehouse import WarehouseOut
        from BE.schemas.product import ProductOut
        from BE.schemas.order import PackageItemOut
        from BE.schemas.user import UserOut

        order_ids = list(set(p["order_id"] for p in combined_packages))
        warehouse_ids = list(set(p["warehouse_id"] for p in combined_packages))
        product_ids = list(set(d["product_id"] for p in combined_packages for d in p["details"]))

        orders = session.query(Order).filter(Order.id.in_(order_ids)).all() if order_ids else []
        user_ids = list(set(o.user_id for o in orders))
        users = session.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        users_by_id = {u.id: UserOut(id=u.id, username=u.username, full_name=u.full_name) for u in users}

        orders_by_id = {}
        for o in orders:
            user_out = users_by_id.get(o.user_id)
            orders_by_id[o.id] = OrderForPackageOut(
                id=o.id,
                user=user_out,
                shipping_address=o.shipping_address,
                total_amount=float(o.total_amount),
                ordered_at=o.ordered_at
            )

        warehouses = WarehouseRepository.list_by_ids(session, warehouse_ids) if warehouse_ids else []
        warehouses_by_id = {w.id: WarehouseOut(id=w.id, name=w.name, region=w.region, address=w.address) for w in warehouses}

        products = session.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
        categories = {c.id: c.name for c in session.query(Category).all()}
        products_out = {
            p.id: ProductOut(
                id=p.id,
                name=p.name,
                category_id=p.category_id,
                category_name=categories.get(p.category_id),
                price=p.price
            )
            for p in products
        }

        result = []
        for p in combined_packages:
            wh_out = warehouses_by_id.get(p["warehouse_id"])
            ord_out = orders_by_id.get(p["order_id"])
            if wh_out and ord_out:
                items_out = []
                for d in p["details"]:
                    prod_out = products_out.get(d["product_id"])
                    if prod_out:
                        items_out.append(
                            PackageItemOut(product=prod_out, quantity=d["quantity"])
                        )
                result.append(
                    PackageFullOut(
                        id=p["id"],
                        warehouse=wh_out,
                        status=p["status"],
                        created_at=p["created_at"],
                        order=ord_out,
                        items=items_out
                    )
                )

        return result
