from fastapi import HTTPException
from sqlalchemy.orm import Session
from BE.repositories.package_repository import PackageRepository
from BE.schemas.package import PackageSimpleOut, PackageStatusUpdateRequest


class PackageService:
    @staticmethod
    def update_package_status(
        session: Session, package_id: int, request: PackageStatusUpdateRequest
    ) -> PackageSimpleOut:
        package = PackageRepository.find_by_id(session, package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Không tìm thấy kiện hàng")

        package.status = request.status
        session.commit()
        session.refresh(package)

        return PackageSimpleOut.model_validate(package)
