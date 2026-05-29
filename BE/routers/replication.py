from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from BE.database import SessionLocal, get_db_node, circuit_breaker
from BE.models.category import Category
from BE.models.replication_log import ReplicationLog
from BE.repositories.category_repository import CategoryRepository
from BE.models.product import Product
from BE.repositories.product_repository import ProductRepository
from BE.repositories.warehouse_repository import WarehouseRepository
from BE.repositories.inventory_repository import InventoryRepository
from BE.models.inventory import Inventory
from BE.models.package_detail import PackageDetail

router = APIRouter(prefix="/replication", tags=["Replication"])

def full_sync_node(node_name: str) -> bool:
    """
    So sánh bảng Category và Product ở Trung tâm và Node đích.
    Đắp dữ liệu nếu thiếu hoặc lệch.
    Trả về True nếu đồng bộ thành công, False nếu có lỗi (Node sập).
    """
    if not circuit_breaker.is_available(node_name):
        print(f"Circuit Breaker: Bỏ qua full sync cho Node [{node_name}] do đang OFFLINE.")
        return False
        
    category_repo = CategoryRepository()
    product_repo = ProductRepository()
    warehouse_repo = WarehouseRepository()
    inventory_repo = InventoryRepository()
    
    with SessionLocal() as main_db:
        main_categories = category_repo.list_all(main_db)
        main_dict = {cat.id: cat for cat in main_categories}
        
        main_products = product_repo.list_all(main_db, include_deleted=True)
        main_prod_dict = {p.id: p for p in main_products}
        
        warehouses = warehouse_repo.list_all(main_db)
        
        try:
            node_session = get_db_node(node_name)
        except ValueError as e:
            print(f"Skipping sync for {node_name}: {e}")
            return False
            
        try:
            with node_session as node_db:
                node_categories = category_repo.list_all(node_db)
                node_dict = {cat.id: cat for cat in node_categories}
                
                # 1. Check for category insertions / updates
                for c_id, c_cat in main_dict.items():
                    if c_id not in node_dict:
                        # Insert category
                        category_repo.create_with_id(node_db, id=c_id, name=c_cat.name)
                    elif node_dict[c_id].name != c_cat.name:
                        # Update category
                        category_repo.update(node_dict[c_id], name=c_cat.name)
                
                # 2. Check for product insertions / updates
                node_products = product_repo.list_all(node_db, include_deleted=True)
                node_prod_dict = {p.id: p for p in node_products}
                
                for p_id, p_prod in main_prod_dict.items():
                    if p_id not in node_prod_dict:
                        # Insert product
                        new_prod = product_repo.create_with_id(
                            node_db,
                            id=p_id,
                            name=p_prod.name,
                            category_id=p_prod.category_id,
                            price=p_prod.price
                        )
                        new_prod.deleted_at = p_prod.deleted_at
                        
                        # Ensure inventory row exists on node DB for this product and its regional warehouses
                        for wh in warehouses:
                            if wh.region.value.lower() == node_name.lower():
                                inv_exists = node_db.query(Inventory).filter(
                                    Inventory.product_id == p_id,
                                    Inventory.warehouse_id == wh.id
                                ).first()
                                if not inv_exists:
                                    inventory_repo.create(
                                        node_db,
                                        product_id=p_id,
                                        warehouse_id=wh.id,
                                        stock_quantity=0
                                    )
                    else:
                        node_prod = node_prod_dict[p_id]
                        if (
                            node_prod.name != p_prod.name or
                            node_prod.category_id != p_prod.category_id or
                            node_prod.price != p_prod.price or
                            node_prod.deleted_at != p_prod.deleted_at
                        ):
                            node_prod.name = p_prod.name
                            node_prod.category_id = p_prod.category_id
                            node_prod.price = p_prod.price
                            node_prod.deleted_at = p_prod.deleted_at
                
                # 3. Check for product deletions (hard delete if not in main DB)
                for n_id, n_prod in node_prod_dict.items():
                    if n_id not in main_prod_dict:
                        # Delete related inventories and package details first to avoid FK issues
                        node_db.query(Inventory).filter(Inventory.product_id == n_id).delete()
                        node_db.query(PackageDetail).filter(PackageDetail.product_id == n_id).delete()
                        node_db.delete(n_prod)
                
                # 4. Check for category deletions
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
