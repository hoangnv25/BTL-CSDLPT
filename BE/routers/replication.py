from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from BE.database import SessionLocal, get_db_node, circuit_breaker
from BE.models.category import Category
from BE.models.replication_log import ReplicationLog
from BE.repositories.category_repository import CategoryRepository

router = APIRouter(prefix="/replication", tags=["Replication"])

def full_sync_node(node_name: str) -> bool:
    """
    So sánh bảng Category ở Trung tâm và Node đích.
    Đắp dữ liệu nếu thiếu hoặc lệch.
    Trả về True nếu đồng bộ thành công, False nếu có lỗi (Node sập).
    """
    if not circuit_breaker.is_available(node_name):
        print(f"Circuit Breaker: Bỏ qua full sync cho Node [{node_name}] do đang OFFLINE.")
        return False
        
    category_repo = CategoryRepository()
    
    with SessionLocal() as main_db:
        main_categories = category_repo.list_all(main_db)
        main_dict = {cat.id: cat for cat in main_categories}
        
        try:
            node_session = get_db_node(node_name)
        except ValueError as e:
            print(f"Skipping sync for {node_name}: {e}")
            return False
            
        try:
            with node_session as node_db:
                node_categories = category_repo.list_all(node_db)
                node_dict = {cat.id: cat for cat in node_categories}
                
                # Check for insertions / updates
                for c_id, c_cat in main_dict.items():
                    if c_id not in node_dict:
                        # Insert
                        category_repo.create_with_id(node_db, id=c_id, name=c_cat.name)
                    elif node_dict[c_id].name != c_cat.name:
                        # Update
                        category_repo.update(node_dict[c_id], name=c_cat.name)
                
                # Check for deletions
                for n_id, n_cat in node_dict.items():
                    if n_id not in main_dict:
                        category_repo.delete(node_db, n_cat)
                        
                node_db.commit()
                print(f"Successfully full synced node: {node_name}")
                
                # Xóa các log bị kẹt của node này
                stmt = select(ReplicationLog).where(
                    ReplicationLog.target_node == node_name,
                    ReplicationLog.status.in_(["PENDING", "FAILED"])
                )
                stuck_logs = main_db.scalars(stmt).all()
                for log in stuck_logs:
                    log.status = "SUCCESS" # Đã sync tay nên không cần chạy nữa
                main_db.commit()
                circuit_breaker.mark_success(node_name)
                return True
                
        except Exception as e:
            circuit_breaker.mark_failure(node_name)
            print(f"Error during full sync for {node_name}: {e}")
            return False


def initial_full_sync():
    nodes = ["north", "central", "south"]
    for node in nodes:
        full_sync_node(node)


@router.get("/sync-node/{node_name}")
def sync_node_api(node_name: str):
    if node_name not in ["north", "central", "south"]:
        raise HTTPException(status_code=400, detail="Invalid node name")
        
    success = full_sync_node(node_name)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi: Không thể kết nối tới site {node_name.upper()} để đồng bộ. Vui lòng kiểm tra lại Node!"
        )
        
    return {"message": f"Đồng bộ thành công cho site {node_name.upper()}"}

@router.get("/failed-nodes")
def get_failed_nodes():
    with SessionLocal() as db:
        stmt = select(ReplicationLog.target_node).where(
            ReplicationLog.status == "FAILED"
        ).distinct()
        failed_nodes = db.scalars(stmt).all()
        return {"failed_nodes": list(failed_nodes)}
