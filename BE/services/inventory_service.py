import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from BE.database import get_db_node, circuit_breaker
from BE.models.inventory import Inventory
from BE.repositories.inventory_repository import InventoryRepository
from BE.schemas.inventory import InventoryOut, InventoryUpdate

logger = logging.getLogger("app")

# ThreadPool dùng chung toàn cục để tránh block luồng chính khi đóng Executor ở mỗi request
inventory_thread_pool = ThreadPoolExecutor(max_workers=20)

def service_log(service_name: str, content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [{service_name}] {content}"
    print(log_line, flush=True)
    logger.info(log_line)


class InventoryService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._inventory_repo = InventoryRepository()
        self._nodes = ["north", "central", "south"]

    def list_inventory(self) -> list[InventoryOut]:
        service_log("InventoryService", "Bắt đầu truy vấn danh sách tồn kho toàn cục song song (Scatter-Gather)...")
        
        def query_node(node: str) -> list:
            if not circuit_breaker.is_available(node):
                service_log("InventoryService", f"Circuit Breaker: Bỏ qua kết nối đến Node [{node}] do đang ở trạng thái OFFLINE.")
                return []
            try:
                node_session = get_db_node(node)
                with node_session:
                    rows = self._inventory_repo.list_all(node_session)
                    circuit_breaker.mark_success(node)
                    return [{
                        "id": r.id,
                        "product_id": r.product_id,
                        "warehouse_id": r.warehouse_id,
                        "stock_quantity": r.stock_quantity,
                        "updated_at": r.updated_at
                    } for r in rows]
            except Exception as e:
                circuit_breaker.mark_failure(node)
                service_log("InventoryService", f"CẢNH BÁO: Node phụ [{node}] bị sập/lỗi kết nối ({e}). Bỏ qua node này.")
                return []

        combined_rows = []
        futures = {inventory_thread_pool.submit(query_node, node): node for node in self._nodes}
        # Tăng timeout lên 2.0s để tránh nghẽn DNS của hệ điều hành hoặc khi DB chịu tải cao
        done, not_done = wait(futures.keys(), timeout=2.0)
        
        for f in done:
            node = futures[f]
            results = f.result()
            service_log("InventoryService", f"Lấy thành công {len(results)} bản ghi tồn kho từ Node phụ: [{node}]")
            for r in results:
                combined_rows.append(InventoryOut.model_validate(r))
                
        for f in not_done:
            node = futures[f]
            circuit_breaker.mark_failure(node)
            service_log("InventoryService", f"TIMEOUT: Node phụ [{node}] không phản hồi trong 2.0s (kẹt DNS/Kết nối). Đánh dấu OFFLINE.")
                    
        return combined_rows

    def list_by_warehouse(self, warehouse_id: int) -> list[InventoryOut]:
        service_log("InventoryService", f"Bắt đầu truy vấn tồn kho cho warehouse_id={warehouse_id}")
        from BE.repositories.warehouse_repository import WarehouseRepository
        wh = WarehouseRepository().find_by_id(self._session, warehouse_id)
        if not wh:
            service_log("InventoryService", f"LỖI: Không tìm thấy kho hàng (ID={warehouse_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng."
            )
        
        node_key = wh.region.value.lower()
        service_log("InventoryService", f"Kho '{wh.name}' thuộc region '{wh.region}' -> Định tuyến truy vấn đến Node phụ: [{node_key}]")
        
        if not circuit_breaker.is_available(node_key):
            service_log("InventoryService", f"Circuit Breaker: Node phụ [{node_key}] đang ở trạng thái OFFLINE. Hủy truy vấn ngay lập tức.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi kết nối phân mảnh: Node [{node_key}] không hoạt động (Circuit Breaker)."
            )
            
        try:
            node_session = get_db_node(node_key)
            with node_session:
                rows = self._inventory_repo.list_by_warehouse(node_session, warehouse_id)
                result = [InventoryOut.model_validate(row) for row in rows]
            circuit_breaker.mark_success(node_key)
            service_log("InventoryService", f"Lấy thành công {len(result)} bản ghi tồn kho cho kho ID={warehouse_id} từ Node: [{node_key}]")
            return result
        except Exception as e:
            circuit_breaker.mark_failure(node_key)
            service_log("InventoryService", f"LỖI: Không thể kết nối tới Node phụ [{node_key}] để đọc tồn kho: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi kết nối phân mảnh: Node [{node_key}] không hoạt động."
            )

    def list_by_product(self, product_id: int) -> list[InventoryOut]:
        service_log("InventoryService", f"Bắt đầu truy vấn tồn kho phân tán song song cho product_id={product_id} (Scatter-Gather)...")
        
        def query_node(node: str) -> list:
            if not circuit_breaker.is_available(node):
                service_log("InventoryService", f"Circuit Breaker: Bỏ qua kết nối đến Node [{node}] do đang ở trạng thái OFFLINE.")
                return []
            try:
                node_session = get_db_node(node)
                with node_session:
                    rows = self._inventory_repo.list_by_product(node_session, product_id)
                    circuit_breaker.mark_success(node)
                    return [{
                        "id": r.id,
                        "product_id": r.product_id,
                        "warehouse_id": r.warehouse_id,
                        "stock_quantity": r.stock_quantity,
                        "updated_at": r.updated_at
                    } for r in rows]
            except Exception as e:
                circuit_breaker.mark_failure(node)
                service_log("InventoryService", f"CẢNH BÁO: Node phụ [{node}] bị sập/lỗi kết nối ({e}). Bỏ qua node này.")
                return []

        combined_rows = []
        futures = {inventory_thread_pool.submit(query_node, node): node for node in self._nodes}
        done, not_done = wait(futures.keys(), timeout=0.5)
        
        for f in done:
            node = futures[f]
            results = f.result()
            service_log("InventoryService", f"Lấy thành công {len(results)} bản ghi từ Node phụ: [{node}] cho sản phẩm ID={product_id}")
            for r in results:
                combined_rows.append(InventoryOut.model_validate(r))
                
        for f in not_done:
            node = futures[f]
            circuit_breaker.mark_failure(node)
            service_log("InventoryService", f"TIMEOUT: Node phụ [{node}] không phản hồi trong 0.5s cho sản phẩm ID={product_id}. Đánh dấu OFFLINE.")
                
        return combined_rows

    def update_inventory(self, body: InventoryUpdate) -> InventoryOut:
        service_log("InventoryService", f"Bắt đầu yêu cầu cập nhật tồn kho cho bản ghi ID={body.id} tại warehouse_id={body.warehouse_id}")
        
        from BE.repositories.warehouse_repository import WarehouseRepository
        wh = WarehouseRepository().find_by_id(self._session, body.warehouse_id)
        if not wh:
            service_log("InventoryService", f"LỖI: Không tìm thấy kho hàng (ID={body.warehouse_id})")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy kho hàng."
            )
            
        target_node = wh.region.value.lower()
        service_log("InventoryService", f"Kho '{wh.name}' thuộc region '{wh.region}' -> Định tuyến cập nhật đến Node phụ: [{target_node}]")
        
        if not circuit_breaker.is_available(target_node):
            service_log("InventoryService", f"Circuit Breaker: Node phụ [{target_node}] đang ở trạng thái OFFLINE. Hủy yêu cầu.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi kết nối phân mảnh: Node [{target_node}] không hoạt động."
            )
            
        # 2. Thực hiện khóa dòng dữ liệu bi quan (SELECT FOR UPDATE) và cập nhật
        node_session = get_db_node(target_node)
        try:
            service_log(
                "InventoryService", 
                f"Đang thực hiện khóa dòng dữ liệu bi quan (SELECT ... FOR UPDATE) trên Node phụ [{target_node}] cho ID={body.id}"
            )
            
            row = node_session.query(Inventory).filter(Inventory.id == body.id).with_for_update().first()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy bản ghi tồn kho tại thời điểm cập nhật."
                )
                
            old_qty = row.stock_quantity
            self._inventory_repo.update_quantity(row, stock_quantity=body.stock_quantity)
            node_session.commit()
            circuit_breaker.mark_success(target_node)
            
            service_log(
                "InventoryService",
                f"Cập nhật thành công tồn kho ID={body.id} tại Node [{target_node}]: Số lượng cũ = {old_qty} -> Số lượng mới = {body.stock_quantity}"
            )
            return InventoryOut.model_validate(row)
        except Exception as e:
            node_session.rollback()
            circuit_breaker.mark_failure(target_node)
            service_log("InventoryService", f"LỖI nghiêm trọng khi cập nhật tồn kho trên Node phụ [{target_node}]: {e}")
            raise e
        finally:
            node_session.close()

    def get_total_stock_by_product(self, product_id: int) -> int:
        service_log("InventoryService", f"Bắt đầu tính tổng tồn kho toàn cục song song cho product_id={product_id} (Scatter-Gather)...")
        
        def query_sum_node(node: str) -> int:
            if not circuit_breaker.is_available(node):
                service_log("InventoryService", f"Circuit Breaker: Bỏ qua kết nối đến Node [{node}] do đang ở trạng thái OFFLINE.")
                return 0
            try:
                node_session = get_db_node(node)
                with node_session:
                    rows = self._inventory_repo.list_by_product(node_session, product_id)
                    node_sum = sum(row.stock_quantity for row in rows)
                    circuit_breaker.mark_success(node)
                    service_log("InventoryService", f"Node phụ [{node}] trả về lượng tồn kho = {node_sum} cho sản phẩm ID={product_id}")
                    return node_sum
            except Exception as e:
                circuit_breaker.mark_failure(node)
                service_log("InventoryService", f"CẢNH BÁO: Node phụ [{node}] bị sập/lỗi kết nối ({e}). Lượng tồn ở node này được coi là 0.")
                return 0

        total_stock = 0
        futures = {inventory_thread_pool.submit(query_sum_node, node): node for node in self._nodes}
        done, not_done = wait(futures.keys(), timeout=0.5)
        
        for f in done:
            total_stock += f.result()
            
        for f in not_done:
            node = futures[f]
            circuit_breaker.mark_failure(node)
            service_log("InventoryService", f"TIMEOUT: Node phụ [{node}] không phản hồi trong 0.5s. Tính tồn kho = 0 và đánh dấu OFFLINE.")
            
        service_log("InventoryService", f"Tổng tồn kho toàn cục của sản phẩm ID={product_id} là: {total_stock}")
        return total_stock

    def get_total_stock_for_products(self, product_ids: list[int]) -> dict[int, int]:
        if not product_ids:
            return {}
            
        service_log("InventoryService", f"Bắt đầu gom tổng tồn kho song song cho {len(product_ids)} sản phẩm (Scatter-Gather)...")
        
        stock_map = {pid: 0 for pid in product_ids}
        
        def query_node_batch(node: str) -> list:
            if not circuit_breaker.is_available(node):
                service_log("InventoryService", f"Circuit Breaker: Bỏ qua kết nối đến Node [{node}] do đang ở trạng thái OFFLINE.")
                return []
            try:
                node_session = get_db_node(node)
                with node_session:
                    stmt = select(Inventory).where(Inventory.product_id.in_(product_ids))
                    rows = list(node_session.scalars(stmt).all())
                    circuit_breaker.mark_success(node)
                    return [{"product_id": r.product_id, "stock_quantity": r.stock_quantity} for r in rows]
            except Exception as e:
                circuit_breaker.mark_failure(node)
                service_log("InventoryService", f"CẢNH BÁO: Node phụ [{node}] bị sập/lỗi kết nối ({e}). Bỏ qua node này khi quét danh sách.")
                return []

        futures = {inventory_thread_pool.submit(query_node_batch, node): node for node in self._nodes}
        done, not_done = wait(futures.keys(), timeout=0.5)
        
        for f in done:
            node = futures[f]
            results = f.result()
            service_log("InventoryService", f"Nhận kết quả lô từ Node phụ: [{node}] ({len(results)} bản ghi)")
            for r in results:
                pid = r["product_id"]
                if pid in stock_map:
                    stock_map[pid] += r["stock_quantity"]
                    
        for f in not_done:
            node = futures[f]
            circuit_breaker.mark_failure(node)
            service_log("InventoryService", f"TIMEOUT: Node phụ [{node}] không phản hồi trong 0.5s khi gom lô. Đánh dấu OFFLINE.")
                    
        service_log("InventoryService", "Hoàn tất gom tồn kho song song.")
        return stock_map
