from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from BE.database import SessionLocal, get_db_node
from BE.models.category import Category
from BE.models.product import Product
from BE.models.replication_log import ReplicationLog
from BE.repositories.category_repository import CategoryRepository
from BE.repositories.product_repository import ProductRepository

router = APIRouter(prefix="/replication", tags=["Replication"])

def full_sync_node(node_name: str) -> bool:
    """
    So sánh bảng Category và Product ở Trung tâm và Node đích.
    Đắp dữ liệu nếu thiếu hoặc lệch.
    Trả về True nếu đồng bộ thành công, False nếu có lỗi (Node sập).
    """
    category_repo = CategoryRepository()
    product_repo = ProductRepository()
    
    with SessionLocal() as main_db:
        # Lấy dữ liệu mẫu từ Trung tâm
        main_categories = category_repo.list_all(main_db)
        main_cat_dict = {cat.id: cat for cat in main_categories}
        
        main_products = product_repo.list_all(main_db, include_deleted=True)
        main_prod_dict = {p.id: p for p in main_products}
        
        try:
            node_session = get_db_node(node_name)
        except ValueError as e:
            print(f"Skipping sync for {node_name}: {e}")
            return False
            
        try:
            with node_session as node_db:
                # 1. Đồng bộ Categories
                node_categories = category_repo.list_all(node_db)
                node_cat_dict = {cat.id: cat for cat in node_categories}
                
                for c_id, c_cat in main_cat_dict.items():
                    if c_id not in node_cat_dict:
                        category_repo.create_with_id(node_db, id=c_id, name=c_cat.name)
                    elif node_cat_dict[c_id].name != c_cat.name:
                        category_repo.update(node_cat_dict[c_id], name=c_cat.name)
                
                for n_id, n_cat in node_cat_dict.items():
                    if n_id not in main_cat_dict:
                        category_repo.delete(node_db, n_cat)

                # 2. Đồng bộ Products
                node_products = product_repo.list_all(node_db, include_deleted=True)
                node_prod_dict = {p.id: p for p in node_products}

                for p_id, p_main in main_prod_dict.items():
                    if p_id not in node_prod_dict:
                        row = product_repo.create_with_id(
                            node_db, 
                            id=p_id, 
                            name=p_main.name, 
                            category_id=p_main.category_id, 
                            price=p_main.price
                        )
                        row.deleted_at = p_main.deleted_at
                    else:
                        p_node = node_prod_dict[p_id]
                        if (p_node.name != p_main.name or 
                            p_node.category_id != p_main.category_id or 
                            p_node.price != p_main.price or 
                            p_node.deleted_at != p_main.deleted_at):
                            
                            product_repo.update(
                                p_node, 
                                name=p_main.name, 
                                category_id=p_main.category_id, 
                                price=p_main.price
                            )
                            p_node.deleted_at = p_main.deleted_at
                
                for p_id, p_node in node_prod_dict.items():
                    if p_id not in main_prod_dict:
                        node_db.delete(p_node)
                        
                node_db.commit()
                print(f"Successfully full synced node: {node_name}")
                
                # Xóa các log bị kẹt của node này
                stmt = select(ReplicationLog).where(
                    ReplicationLog.target_node == node_name,
                    ReplicationLog.status.in_(["PENDING", "FAILED"])
                )
                stuck_logs = main_db.scalars(stmt).all()
                for log in stuck_logs:
                    log.status = "SUCCESS" 
                main_db.commit()
                return True
                
        except Exception as e:
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
