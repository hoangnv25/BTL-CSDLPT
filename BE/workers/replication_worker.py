import asyncio
from sqlalchemy import select
from datetime import datetime, timezone
import json

from BE.database import SessionLocal, get_db_node, circuit_breaker
from BE.models.replication_log import ReplicationLog
from BE.repositories.category_repository import CategoryRepository
from BE.repositories.product_repository import ProductRepository
from BE.routers.websocket import manager

class ReplicationWorker:
    def __init__(self):
        self._category_repo = CategoryRepository()
        self._product_repo = ProductRepository()
        self._trigger_event = asyncio.Event()

    def trigger(self):
        self._trigger_event.set()

    async def run(self):
        loop = asyncio.get_running_loop()
        while True:
            try:
                # Điều này giúp Event Loop của Uvicorn không bị block, phản hồi API của Main DB luôn tức thời!
                await asyncio.to_thread(self.process_logs, loop)
            except Exception as e:
                print(f"Replication worker error: {e}")
            
            # Chạy ngay lập tức khi được trigger, hoặc tự động quét lại sau 3.0 giây
            try:
                await asyncio.wait_for(self._trigger_event.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                pass
            finally:
                self._trigger_event.clear()

    def process_logs(self, loop):
        with SessionLocal() as db:
            # Lấy các log PENDING hoặc FAILED (retry_count < 3), lọc next_retry_at <= now
            now = datetime.utcnow()
            stmt = select(ReplicationLog).where(
                ReplicationLog.status.in_(["PENDING", "FAILED"]),
                ReplicationLog.retry_count < 3,
                ReplicationLog.next_retry_at <= now
            )
            logs = db.scalars(stmt).all()

            for log in logs:
                success = self._sync_log(log)
                node = log.target_node
                action = log.action
                table_name = log.table_name

                if success:
                    log.status = "SUCCESS"
                    # Nếu là sync stats thành công sau khi fail, bắn tin mừng
                    if action == "SYNC_STATS":
                        asyncio.run_coroutine_threadsafe(manager.broadcast({
                            "type": "SYNC_SUCCESS",
                            "node": node,
                            "action": action,
                            "table": table_name,
                            "message": f"Đã cập nhật bù thành công dữ liệu cho Node {node}!"
                        }), loop)
                else:
                    log.retry_count += 1
                    log.status = "FAILED"
                    # Lưu trữ dữ liệu ra các biến trước khi session bị đóng để tránh lỗi DetachedInstanceError
                    retry_count = log.retry_count
                    # Gửi thông báo đến FE từ luồng phụ (Worker) về luồng chính (Main Event Loop)
                    asyncio.run_coroutine_threadsafe(self._notify_fe(node, action, table_name, retry_count), loop)
                
            db.commit()

    def sync_logs_immediately(self, log_ids: list[int]) -> dict:
        """
        Đồng bộ ngay lập tức danh sách log và trả về trạng thái từng node.
        Dùng cho phản hồi API ngay lập tức cho người dùng.
        """
        results = {}
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        with SessionLocal() as db:
            stmt = select(ReplicationLog).where(ReplicationLog.id.in_(log_ids))
            logs = db.scalars(stmt).all()
            
            for log in logs:
                if log.status == "SUCCESS":
                    results[log.target_node] = "SUCCESS"
                    continue
                    
                success = self._sync_log(log)
                node = log.target_node
                action = log.action
                table_name = log.table_name

                if success:
                    log.status = "SUCCESS"
                    results[node] = "SUCCESS"
                else:
                    log.retry_count += 1
                    log.status = "FAILED"
                    results[node] = "FAILED"
                    
                    retry_count = log.retry_count
                    if loop:
                        asyncio.run_coroutine_threadsafe(self._notify_fe(node, action, table_name, retry_count), loop)
            
            db.commit()
        return results

    def _sync_log(self, log: ReplicationLog) -> bool:
        if not circuit_breaker.is_available(log.target_node):
            print(f"Circuit Breaker: Bỏ qua sync log {log.id} for Node [{log.target_node}] do đang OFFLINE.")
            return False
        
        # Xử lý riêng cho hành động SYNC_STATS
        if log.action == "SYNC_STATS":
            try:
                from BE.services.stats_service import StatsService
                print(f"ReplicationWorker: Đang đồng bộ bù Stats cho Node [{log.target_node}]...")
                
                # Giải mã các tham số thời gian từ payload
                params = {}
                if log.data_payload:
                    try:
                        params = json.loads(log.data_payload)
                    except Exception as pe:
                        print(f"ReplicationWorker: Lỗi parse data_payload: {pe}")
                
                spec_date_str = params.get("specific_date")
                spec_date = datetime.strptime(spec_date_str, "%Y-%m-%d").date() if spec_date_str else None
                spec_month = params.get("specific_month")
                spec_year = params.get("specific_year")

                StatsService.sync_node_stats(
                    log.target_node,
                    specific_date=spec_date,
                    specific_month=spec_month,
                    specific_year=spec_year
                )
                return True
            except Exception as e:
                print(f"ReplicationWorker: Lỗi sync bù Stats cho [{log.target_node}]: {e}")
                return False
            
        try:
            node_session = get_db_node(log.target_node)
            with node_session as session:
                if log.table_name == "category":
                    if log.action == "INSERT":
                        data = json.loads(log.data_payload)
                        existing = self._category_repo.find_by_id(session, log.record_id)
                        if not existing:
                            self._category_repo.create_with_id(session, id=log.record_id, name=data["name"])
                    
                    elif log.action == "UPDATE":
                        data = json.loads(log.data_payload)
                        existing = self._category_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._category_repo.update(existing, name=data["name"])
                        else:
                            self._category_repo.create_with_id(session, id=log.record_id, name=data["name"])
                            
                    elif log.action == "DELETE":
                        existing = self._category_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._category_repo.delete(session, existing)

                elif log.table_name == "product":
                    if log.action == "INSERT":
                        data = json.loads(log.data_payload)
                        existing = self._product_repo.find_by_id(session, log.record_id)
                        if not existing:
                            self._product_repo.create_with_id(
                                session, 
                                id=log.record_id, 
                                name=data["name"],
                                category_id=data["category_id"],
                                price=data["price"]
                            )
                        self._ensure_inventory_for_product(session, log.record_id, log.target_node)
                    
                    elif log.action == "UPDATE":
                        data = json.loads(log.data_payload)
                        existing = self._product_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._product_repo.update(
                                existing, 
                                name=data["name"],
                                category_id=data["category_id"],
                                price=data["price"]
                            )
                        else:
                            self._product_repo.create_with_id(
                                session, 
                                id=log.record_id, 
                                name=data["name"],
                                category_id=data["category_id"],
                                price=data["price"]
                            )
                            self._ensure_inventory_for_product(session, log.record_id, log.target_node)

                    elif log.action == "DELETE":
                        existing = self._product_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._product_repo.delete(session, existing)

                    elif log.action == "RESTORE":
                        existing = self._product_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._product_repo.restore(session, existing)
                            
                session.commit()
                circuit_breaker.mark_success(log.target_node)
                return True
        except Exception as e:
            circuit_breaker.mark_failure(log.target_node)
            print(f"Sync failed for node {log.target_node}, log {log.id}: {e}")
            return False

    def _ensure_inventory_for_product(self, session, product_id: int, target_node: str):
        with SessionLocal() as main_db:
            from BE.repositories.warehouse_repository import WarehouseRepository
            from BE.models.inventory import Inventory
            from BE.repositories.inventory_repository import InventoryRepository
            
            warehouses = WarehouseRepository().list_all(main_db)
            for wh in warehouses:
                if wh.region.value.lower() == target_node.lower():
                    inv_exists = session.query(Inventory).filter(
                        Inventory.product_id == product_id,
                        Inventory.warehouse_id == wh.id
                    ).first()
                    if not inv_exists:
                        InventoryRepository().create(
                            session,
                            product_id=product_id,
                            warehouse_id=wh.id,
                            stock_quantity=0
                        )

    async def _notify_fe(self, node: str, action: str, table_name: str, retry_count: int):
        message = {
            "type": "SYNC_ERROR",
            "node": node,
            "action": action,
            "table": table_name,
            "retry_count": retry_count,
            "message": f"Không thể cập nhật thao tác {action} trên bảng {table_name} tới site {node}. Đang thử lại lần {retry_count}/3."
        }
        await manager.broadcast(message)

# Global worker instance
replication_worker = ReplicationWorker()
