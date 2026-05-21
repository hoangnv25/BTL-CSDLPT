from fastapi import HTTPException
from sqlalchemy.orm import Session
from BE.repositories.package_repository import PackageRepository
from BE.schemas.package import PackageSimpleOut, PackageStatusUpdateRequest, PackageFullOut, OrderForPackageOut


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

    @staticmethod
    def list_packages(session: Session, warehouse_id: int | None = None) -> list[PackageFullOut]:
        from BE.models.order import Order
        from BE.models.user import User
        from BE.models.package import Package
        from BE.models.package_detail import PackageDetail
        from BE.models.product import Product
        from BE.models.category import Category
        from BE.models.warehouse import Warehouse
        from BE.schemas.warehouse import WarehouseOut
        from BE.schemas.product import ProductOut
        from BE.schemas.order import PackageItemOut
        from BE.schemas.user import UserOut

        # 1. Query packages
        query = session.query(Package)
        if warehouse_id is not None:
            query = query.filter(Package.warehouse_id == warehouse_id)
        packages = query.order_by(Package.id.desc()).all()

        if not packages:
            return []

        # 2. Extract IDs
        package_ids = [p.id for p in packages]
        order_ids = list(set(p.order_id for p in packages))
        warehouse_ids = list(set(p.warehouse_id for p in packages))

        # 3. Query orders & users
        orders = session.query(Order).filter(Order.id.in_(order_ids)).all()
        user_ids = list(set(o.user_id for o in orders))
        users = session.query(User).filter(User.id.in_(user_ids)).all()
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

        # 4. Query warehouses
        warehouses = session.query(Warehouse).filter(Warehouse.id.in_(warehouse_ids)).all()
        warehouses_by_id = {w.id: WarehouseOut(id=w.id, name=w.name, region=w.region, address=w.address) for w in warehouses}

        # 5. Query details, products & categories
        details = session.query(PackageDetail).filter(PackageDetail.package_id.in_(package_ids)).all()
        product_ids = list(set(d.product_id for d in details))
        products = session.query(Product).filter(Product.id.in_(product_ids)).all()
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

        # 6. Group details by package_id
        details_by_package = {}
        for d in details:
            if d.package_id not in details_by_package:
                details_by_package[d.package_id] = []
            prod_out = products_out.get(d.product_id)
            if prod_out:
                details_by_package[d.package_id].append(
                    PackageItemOut(product=prod_out, quantity=d.quantity)
                )

        # 7. Assemble final result
        result = []
        for p in packages:
            wh_out = warehouses_by_id.get(p.warehouse_id)
            ord_out = orders_by_id.get(p.order_id)
            if wh_out and ord_out:
                result.append(
                    PackageFullOut(
                        id=p.id,
                        warehouse=wh_out,
                        status=p.status,
                        created_at=p.created_at,
                        order=ord_out,
                        items=details_by_package.get(p.id, [])
                    )
                )

        return result
