from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import json

from BE.repositories.category_repository import CategoryRepository
from BE.repositories.product_repository import ProductRepository
from BE.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from BE.models.replication_log import ReplicationLog
from BE.workers.replication_worker import replication_worker

class CategoryService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._category_repo = CategoryRepository()
        self._product_repo = ProductRepository()
        self._nodes = ["north", "central_region", "south"]

    def _add_replication_logs(self, action: str, record_id: int, data_payload: str | None = None):
        for node in self._nodes:
            log = ReplicationLog(
                table_name="category",
                record_id=record_id,
                action=action,
                data_payload=data_payload,
                target_node=node,
                status="PENDING"
            )
            self._session.add(log)

    def create_category(self, body: CategoryCreate) -> CategoryOut:
        row = self._category_repo.create(self._session, name=body.name.strip())
        self._session.flush() # ensure row has id
        
        self._add_replication_logs(
            action="INSERT", 
            record_id=row.id, 
            data_payload=json.dumps({"name": row.name})
        )
        
        self._session.commit()
        replication_worker.trigger() # Kích hoạt đồng bộ lập tức
        self._session.refresh(row)
        return CategoryOut.model_validate(row)

    def list_categories(self) -> list[CategoryOut]:
        rows = self._category_repo.list_all(self._session)
        return [CategoryOut.model_validate(row) for row in rows]

    def update_category(self, id: int, body: CategoryUpdate) -> CategoryOut:
        row = self._category_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        self._category_repo.update(row, name=body.name.strip())
        
        self._add_replication_logs(
            action="UPDATE", 
            record_id=row.id, 
            data_payload=json.dumps({"name": row.name})
        )
        
        self._session.commit()
        replication_worker.trigger() # Kích hoạt đồng bộ lập tức
        self._session.refresh(row)
        return CategoryOut.model_validate(row)

    def delete_category(self, id: int) -> dict[str, str]:
        row = self._category_repo.find_by_id(self._session, id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy danh mục sản phẩm.",
            )

        has_products = self._product_repo.list_by_category(self._session, id)
        if has_products:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa danh mục vì vẫn còn sản phẩm.",
            )

        self._category_repo.delete(self._session, row)
        
        self._add_replication_logs(
            action="DELETE", 
            record_id=id
        )
        
        self._session.commit()
        replication_worker.trigger() # Kích hoạt đồng bộ lập tức
        return {"message": "Xóa danh mục thành công."}
