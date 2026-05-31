from sqlalchemy import select
from sqlalchemy.orm import Session
from BE.models.warehouse import Warehouse, RegionEnum
from BE.database import get_db_node, circuit_breaker, engines

class WarehouseRepository:
    @staticmethod
    def create(session: Session, *, name: str, region: RegionEnum, address: str) -> Warehouse:
        row = Warehouse(name=name, region=region, address=address)
        session.add(row)
        session.flush()
        return row

    @staticmethod
    def list_all(session: Session) -> list[Warehouse]:
        # Kiểm tra xem session hiện tại có phải là Main DB hay không
        is_main = (session.bind == engines.get("main"))
        
        if is_main:
            # Thu thập song song/tuần tự dữ liệu từ cả 3 node nhánh (Scatter-Gather)
            all_warehouses = []
            for node in ["north", "central", "south"]:
                if not circuit_breaker.is_available(node):
                    continue
                try:
                    temp_session = get_db_node(node)
                    try:
                        stmt = select(Warehouse).order_by(Warehouse.id)
                        rows = temp_session.scalars(stmt).all()
                        for r in rows:
                            # Trục xuất (expunge) thực thể ra khỏi session tạm thời
                            # để tránh lỗi DetachedInstanceError khi đóng session
                            temp_session.expunge(r)
                            all_warehouses.append(r)
                    finally:
                        temp_session.close()
                except Exception:
                    pass
            # Sắp xếp danh sách gộp theo ID để đảm bảo thứ tự nhất quán
            all_warehouses.sort(key=lambda w: w.id)
            return all_warehouses
        else:
            # Đối với Node chi nhánh: Chỉ lấy dữ liệu kho hàng cục bộ của Node đó
            stmt = select(Warehouse).order_by(Warehouse.id)
            return list(session.scalars(stmt).all())

    @staticmethod
    def find_by_id(session: Session, id: int) -> Warehouse | None:
        is_main = (session.bind == engines.get("main"))
        
        # Bước 1: Tìm kiếm cục bộ trên session hiện tại (Local First) nếu không phải là Main DB
        if not is_main:
            try:
                stmt = select(Warehouse).where(Warehouse.id == id)
                row = session.scalar(stmt)
                if row is not None:
                    return row
            except Exception:
                pass
        
        # Bước 2: Tìm kiếm trên các Node phụ (Scatter-Gather / Fallback)
        for node in ["north", "central", "south"]:
            if not circuit_breaker.is_available(node):
                continue
            try:
                temp_session = get_db_node(node)
                try:
                    node_row = temp_session.scalar(select(Warehouse).where(Warehouse.id == id))
                    if node_row is not None:
                        temp_session.expunge(node_row)
                        return node_row
                finally:
                    temp_session.close()
            except Exception:
                pass
        return None

    @staticmethod
    def list_by_ids(session: Session, ids: list[int]) -> list[Warehouse]:
        """Lấy danh sách các kho theo danh sách ID (dùng trong truy vấn gộp)"""
        all_wh = WarehouseRepository.list_all(session)
        id_set = set(ids)
        return [w for w in all_wh if w.id in id_set]

    @staticmethod
    def update(row: Warehouse, *, name: str, region: RegionEnum, address: str) -> Warehouse:
        row.name = name
        row.region = region
        row.address = address
        return row
