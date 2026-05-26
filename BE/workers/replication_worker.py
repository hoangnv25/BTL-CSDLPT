import asyncio
from sqlalchemy import select
from datetime import datetime, timezone
import json

from BE.database import SessionLocal, get_db_node
from BE.models.replication_log import ReplicationLog
from BE.repositories.category_repository import CategoryRepository
from BE.routers.websocket import manager

class ReplicationWorker:
    def __init__(self):
        self._category_repo = CategoryRepository()
        self._trigger_event = asyncio.Event()

    def trigger(self):
        self._trigger_event.set()

    async def run(self):
        while True:
            try:
                self.process_logs()
            except Exception as e:
                print(f"Replication worker error: {e}")
            
            # Chạy ngay lập tức khi được trigger, hoặc tự động quét lại sau 60 giây
            try:
                await asyncio.wait_for(self._trigger_event.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                pass
            finally:
                self._trigger_event.clear()

    def process_logs(self):
        with SessionLocal() as db:
            # Lấy các log PENDING hoặc FAILED (retry_count < 3), lọc next_retry_at <= now
            now = datetime.now(timezone.utc)
            stmt = select(ReplicationLog).where(
                ReplicationLog.status.in_(["PENDING", "FAILED"]),
                ReplicationLog.retry_count < 3,
                ReplicationLog.next_retry_at <= now
            )
            logs = db.scalars(stmt).all()

            for log in logs:
                success = self._sync_log(log)
                if success:
                    log.status = "SUCCESS"
                else:
                    log.retry_count += 1
                    log.status = "FAILED"
                    # Notify FE
                    asyncio.create_task(self._notify_fe(log))
                
            db.commit()

    def _sync_log(self, log: ReplicationLog) -> bool:
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
                            # If it doesn't exist on node but we got an update, it means insert was missed.
                            self._category_repo.create_with_id(session, id=log.record_id, name=data["name"])
                            
                    elif log.action == "DELETE":
                        existing = self._category_repo.find_by_id(session, log.record_id)
                        if existing:
                            self._category_repo.delete(session, existing)
                            
                session.commit()
                return True
        except Exception as e:
            print(f"Sync failed for node {log.target_node}, log {log.id}: {e}")
            return False

    async def _notify_fe(self, log: ReplicationLog):
        message = {
            "type": "SYNC_ERROR",
            "node": log.target_node,
            "action": log.action,
            "table": log.table_name,
            "retry_count": log.retry_count,
            "message": f"Không thể đồng bộ thao tác {log.action} trên bảng {log.table_name} tới site {log.target_node}. Đang thử lại lần {log.retry_count}/3."
        }
        await manager.broadcast(message)

# Global worker instance
replication_worker = ReplicationWorker()
