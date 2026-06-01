import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed

from BE.database import get_db_node, circuit_breaker
from BE.models.stats import PackageSalesStat
from BE.models.product import Product
from BE.repositories.warehouse_repository import WarehouseRepository

logger = logging.getLogger("app")

def stats_log(content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [StatsService] {content}"
    print(log_line, flush=True)
    logger.info(log_line)

class StatsService:
    @staticmethod
    def update_stats(node_session: Session, product_id: int, warehouse_id: int, quantity: int, revenue: float, package_count: int = 0, delivered_at: date = None):
        """Cập nhật thống kê bán hàng và số lượng kiện hàng (Upsert)"""
        if not delivered_at:
            delivered_at = date.today()
        
        try:
            # Sử dụng ON DUPLICATE KEY UPDATE của MySQL
            stmt = text("""
                INSERT INTO package_sales_stats (product_id, warehouse_id, delivered_at, quantity, revenue, package_count)
                VALUES (:product_id, :warehouse_id, :delivered_at, :quantity, :revenue, :package_count)
                ON DUPLICATE KEY UPDATE 
                    quantity = quantity + VALUES(quantity),
                    revenue = revenue + VALUES(revenue),
                    package_count = package_count + VALUES(package_count)
            """)
            node_session.execute(stmt, {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "delivered_at": delivered_at,
                "quantity": quantity,
                "revenue": revenue,
                "package_count": package_count
            })
        except Exception as e:
            stats_log(f"LỖI khi cập nhật stats cho SP ID={product_id}: {e}")
            raise e

    @staticmethod
    def update_product_sales(node_session: Session, product_id: int, warehouse_id: int, quantity: int, revenue: float, delivered_at: date = None):
        """Hàm cũ để tương thích với các phần chưa cập nhật"""
        return StatsService.update_stats(node_session, product_id, warehouse_id, quantity, revenue, 0, delivered_at)

    @staticmethod
    def get_top_products(
        period: str = "day", 
        warehouse_id: Optional[int] = None,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy top sản phẩm bán chạy.
        specific_date: YYYY-MM-DD
        specific_month: 1-12 (phải đi kèm specific_year)
        specific_year: YYYY
        """
        today = date.today()
        start_date = today
        end_date = today

        # 1. Xác định khoảng thời gian dựa trên các tham số cụ thể hoặc period
        if specific_date:
            start_date = specific_date
            end_date = specific_date
        elif specific_month and specific_year:
            start_date = date(specific_year, specific_month, 1)
            if specific_month == 12:
                end_date = date(specific_year, 12, 31)
            else:
                try:
                    end_date = date(specific_year, specific_month + 1, 1) - timedelta(days=1)
                except ValueError:
                    end_date = date(specific_year, 12, 31)
        elif specific_year:
            start_date = date(specific_year, 1, 1)
            end_date = date(specific_year, 12, 31)
        else:
            # Fallback về period mặc định (từ X ngày trước đến nay)
            end_date = today
            if period == "week":
                start_date = today - timedelta(days=7)
            elif period == "month":
                # Lấy từ đầu tháng đến cuối tháng của tháng hiện tại
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = date(today.year, 12, 31)
                else:
                    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            elif period == "year":
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31)
            else: # day
                start_date = today
        
        # Xác định Node cần truy vấn
        from BE.database import SessionLocal
        nodes_to_query = ["north", "central", "south"]
        
        if warehouse_id:
            main_db = SessionLocal()
            wh = WarehouseRepository.find_by_id(main_db, warehouse_id)
            if wh:
                nodes_to_query = [wh.region.value.lower()]
            main_db.close()

        all_node_stats = []

        def query_node(node_key: str):
            if not circuit_breaker.is_available(node_key):
                return []
            try:
                node_session = get_db_node(node_key)
                with node_session:
                    query = node_session.query(
                        PackageSalesStat.product_id,
                        func.sum(PackageSalesStat.quantity).label("total_qty")
                    ).filter(PackageSalesStat.delivered_at >= start_date)\
                     .filter(PackageSalesStat.delivered_at <= end_date)
                    
                    if warehouse_id:
                        query = query.filter(PackageSalesStat.warehouse_id == warehouse_id)
                        
                    results = query.group_by(PackageSalesStat.product_id).all()
                    return [{"product_id": r[0], "quantity": int(r[1])} for r in results]
            except Exception as e:
                stats_log(f"CẢNH BÁO: Lỗi truy vấn stats từ Node [{node_key}]: {e}")
                return []

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_node = {executor.submit(query_node, node): node for node in nodes_to_query}
            for future in as_completed(future_to_node):
                all_node_stats.extend(future.result())

        # Merge
        aggregated = {}
        for item in all_node_stats:
            pid = item["product_id"]
            aggregated[pid] = aggregated.get(pid, 0) + item["quantity"]

        sorted_pids = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not sorted_pids:
            return []

        final_results = []
        main_db = SessionLocal()
        try:
            for pid, qty in sorted_pids:
                product = main_db.query(Product).filter(Product.id == pid).first()
                if product:
                    final_results.append({
                        "product_id": pid,
                        "product_name": product.name,
                        "price": float(product.price),
                        "total_sold": qty
                    })
        finally:
            main_db.close()

        return final_results

    @staticmethod
    def get_revenue_stats(
        period: str = "day", 
        warehouse_id: Optional[int] = None,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tính toán doanh thu.
        """
        today = date.today()
        start_date = today
        end_date = today

        if specific_date:
            start_date = specific_date
            end_date = specific_date
        elif specific_month and specific_year:
            start_date = date(specific_year, specific_month, 1)
            if specific_month == 12:
                end_date = date(specific_year, 12, 31)
            else:
                try:
                    end_date = date(specific_year, specific_month + 1, 1) - timedelta(days=1)
                except ValueError:
                    end_date = date(specific_year, 12, 31)
        elif specific_year:
            start_date = date(specific_year, 1, 1)
            end_date = date(specific_year, 12, 31)
        else:
            end_date = today
            if period == "week":
                start_date = today - timedelta(days=7)
            elif period == "month":
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = date(today.year, 12, 31)
                else:
                    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            elif period == "year":
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31)
            else:
                start_date = today

        from BE.database import SessionLocal
        main_db = SessionLocal()
        
        try:
            nodes_to_query = ["north", "central", "south"]
            if warehouse_id:
                wh = WarehouseRepository.find_by_id(main_db, warehouse_id)
                if not wh:
                    return {"error": "Warehouse not found"}
                nodes_to_query = [wh.region.value.lower()]

            total_revenue = 0.0
            total_packages = 0

            def query_revenue_node(node_key: str):
                if not circuit_breaker.is_available(node_key):
                    return 0.0, 0
                
                rev = 0.0
                pkg_count = 0
                
                try:
                    node_session = get_db_node(node_key)
                    with node_session:
                        # Tính doanh thu và tổng kiện hàng trực tiếp từ bảng stats tập hợp
                        try:
                            query_stats = node_session.query(
                                func.sum(PackageSalesStat.revenue).label("rev"),
                                func.sum(PackageSalesStat.package_count).label("pkgs")
                            ).filter(PackageSalesStat.delivered_at >= start_date)\
                             .filter(PackageSalesStat.delivered_at <= end_date)
                            
                            if warehouse_id:
                                query_stats = query_stats.filter(PackageSalesStat.warehouse_id == warehouse_id)
                            
                            res = query_stats.first()
                            rev = float(res.rev or 0.0)
                            pkg_count = int(res.pkgs or 0)
                        except Exception as e:
                            stats_log(f"Lỗi truy vấn Thống kê tại Node [{node_key}]: {e}")
                            
                        return rev, pkg_count
                except Exception as e:
                    stats_log(f"LỖI KẾT NỐI Node [{node_key}] khi lấy doanh thu: {e}")
                    return 0.0, 0

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(query_revenue_node, node): node for node in nodes_to_query}
                for future in as_completed(futures):
                    rev, pkgs = future.result()
                    total_revenue += rev
                    total_packages += pkgs

            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "warehouse_id": warehouse_id or "All",
                "total_packages": total_packages,
                "total_revenue": total_revenue
            }
        finally:
            main_db.close()
