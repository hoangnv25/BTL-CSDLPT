import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed

from BE.database import get_db_node, circuit_breaker
from BE.models.stats import ProductSalesStat, WarehousePerformanceStat
from BE.models.product import Product
from BE.models.replication_log import ReplicationLog
from BE.repositories.warehouse_repository import WarehouseRepository

logger = logging.getLogger("app")

def stats_log(content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [StatsService] {content}"
    print(log_line, flush=True)
    logger.info(log_line)

class StatsService:
    @staticmethod
    def get_top_products(
        period: str = "day", 
        warehouse_id: Optional[int] = None,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy top sản phẩm bán chạy TỪ DATABASE TẬP TRUNG.
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
            if period == "month":
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
        
        from BE.database import SessionLocal
        main_db = SessionLocal()
        
        try:
            query = main_db.query(
                ProductSalesStat.product_id,
                func.sum(ProductSalesStat.quantity).label("total_qty")
            ).filter(ProductSalesStat.delivered_at >= start_date)\
             .filter(ProductSalesStat.delivered_at <= end_date)
            
            if warehouse_id:
                query = query.filter(ProductSalesStat.warehouse_id == warehouse_id)
                
            results = query.group_by(ProductSalesStat.product_id)\
                          .order_by(text("total_qty DESC"))\
                          .limit(10).all()

            stats_log(f"Lấy Top Products: Start={start_date}, End={end_date}, Warehouse={warehouse_id or 'All'} -> Tìm thấy {len(results)} sản phẩm")

            if not results:
                return []

            final_results = []
            for r in results:
                pid = r[0]
                qty = int(r[1])
                product = main_db.query(Product).filter(Product.id == pid).first()
                if product:
                    final_results.append({
                        "product_id": pid,
                        "product_name": product.name,
                        "price": float(product.price),
                        "total_sold": qty
                    })
            return final_results
        finally:
            main_db.close()

    @staticmethod
    def get_revenue_stats(
        period: str = "day", 
        warehouse_id: Optional[int] = None,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Tính toán doanh thu TỪ DATABASE TẬP TRUNG.
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
            if period == "month":
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
            query = main_db.query(
                func.sum(WarehousePerformanceStat.total_revenue).label("rev"),
                func.sum(WarehousePerformanceStat.package_count).label("pkgs")
            ).filter(WarehousePerformanceStat.delivered_at >= start_date)\
             .filter(WarehousePerformanceStat.delivered_at <= end_date)
            
            if warehouse_id:
                query = query.filter(WarehousePerformanceStat.warehouse_id == warehouse_id)
            
            res = query.first()
            total_revenue = float(res.rev or 0.0)
            total_packages = int(res.pkgs or 0)

            stats_log(f"Lấy Revenue: Start={start_date}, End={end_date}, Warehouse={warehouse_id or 'All'} -> Doanh thu={total_revenue}, Kiện={total_packages}")

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

    @staticmethod
    def sync_all_stats_to_central(
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ):
        """
        Chạy truy vấn phân tán tới các node để lấy thông tin kiện đã giao và tổng hợp về 2 bảng thống kê tại DB tập trung.
        """
        stats_log("BẮT ĐẦU TỔNG HỢP THỐNG KÊ TỪ CÁC NODE VỀ DB TẬP TRUNG...")
        
        import json
        from BE.database import SessionLocal
        main_db = SessionLocal()
        
        nodes = ["north", "central", "south"]
        log_ids = []

        try:
            # 1. Tạo bản ghi ReplicationLog cho tất cả các node với trạng thái PENDING
            for node_key in nodes:
                payload = {}
                if specific_date:
                    payload["specific_date"] = specific_date.isoformat()
                if specific_month:
                    payload["specific_month"] = specific_month
                if specific_year:
                    payload["specific_year"] = specific_year

                log = ReplicationLog(
                    table_name="stats",
                    record_id=0,
                    action="SYNC_STATS",
                    target_node=node_key,
                    status="PENDING",
                    retry_count=0,
                    data_payload=json.dumps(payload) if payload else None
                )
                main_db.add(log)
                main_db.flush() # Để lấy ID
                log_ids.append(log.id)
            
            main_db.commit()

            # 2. Gọi Worker để xử lý đồng bộ ngay lập tức
            from BE.workers.replication_worker import replication_worker
            results = replication_worker.sync_logs_immediately(log_ids)

            return results
        finally:
            main_db.close()

    @staticmethod
    def sync_node_stats(
        node_key: str,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ):
        """Đồng bộ bù cho 1 Node cụ thể (thường gọi từ ReplicationWorker)"""
        from BE.database import SessionLocal
        main_db = SessionLocal()
        try:
            StatsService._sync_single_node(
                node_key, 
                main_db,
                specific_date=specific_date,
                specific_month=specific_month,
                specific_year=specific_year
            )
        finally:
            main_db.close()

    @staticmethod
    def _sync_single_node(
        node_key: str, 
        main_db: Session,
        specific_date: Optional[date] = None,
        specific_month: Optional[int] = None,
        specific_year: Optional[int] = None
    ) -> tuple[int, int]:
        """Logic lõi để sync 1 node (Private method)"""
        stats_log(f"Đang đồng bộ dữ liệu Node: {node_key} (Date={specific_date}, Month={specific_month}, Year={specific_year})")
        try:
            from BE.database import get_db_node
            node_session = get_db_node(node_key)
            
            # Xây dựng điều kiện lọc thời gian động trên Node nhánh
            where_clauses = ["p.status = 'Delivered'"]
            sql_params = {}
            
            if specific_date:
                where_clauses.append("DATE(p.delivered_at) = :spec_date")
                sql_params["spec_date"] = specific_date
            elif specific_month and specific_year:
                where_clauses.append("YEAR(p.delivered_at) = :spec_year AND MONTH(p.delivered_at) = :spec_month")
                sql_params["spec_month"] = specific_month
                sql_params["spec_year"] = specific_year
            elif specific_year:
                where_clauses.append("YEAR(p.delivered_at) = :spec_year")
                sql_params["spec_year"] = specific_year
            else:
                # Mặc định quét cửa sổ trượt 3 ngày gần nhất để đảm bảo hiệu năng
                where_clauses.append("p.delivered_at >= DATE_SUB(NOW(), INTERVAL 3 DAY)")
                
            where_str = " AND ".join(where_clauses)
            
            # 1. Tổng hợp chi tiết sản phẩm
            stmt_products = text(f"""
                SELECT 
                    pd.product_id, 
                    p.warehouse_id, 
                    DATE(p.delivered_at) as del_date,
                    SUM(pd.quantity) as qty,
                    SUM(pd.quantity * prod.price) as rev
                FROM packages p
                JOIN package_details pd ON p.id = pd.package_id
                JOIN products prod ON pd.product_id = prod.id
                WHERE {where_str}
                GROUP BY pd.product_id, p.warehouse_id, del_date
            """)
            
            product_rows = node_session.execute(stmt_products, sql_params).fetchall()
            for row in product_rows:
                upsert_prod = text("""
                    INSERT INTO product_stats (product_id, warehouse_id, delivered_at, quantity, revenue)
                    VALUES (:pid, :wid, :dat, :qty, :rev)
                    ON DUPLICATE KEY UPDATE 
                        quantity = VALUES(quantity),
                        revenue = VALUES(revenue)
                """)
                main_db.execute(upsert_prod, {
                    "pid": row.product_id,
                    "wid": row.warehouse_id,
                    "dat": row.del_date,
                    "qty": row.qty,
                    "rev": row.rev
                })
            
            # 2. Tổng hợp hiệu suất kho
            stmt_warehouse = text(f"""
                SELECT 
                    p.warehouse_id, 
                    DATE(p.delivered_at) as del_date,
                    SUM(pd.quantity * prod.price) as total_rev,
                    COUNT(DISTINCT p.id) as pkg_count
                FROM packages p
                JOIN package_details pd ON p.id = pd.package_id
                JOIN products prod ON pd.product_id = prod.id
                WHERE {where_str}
                GROUP BY p.warehouse_id, del_date
            """)
            
            warehouse_rows = node_session.execute(stmt_warehouse, sql_params).fetchall()
            for row in warehouse_rows:
                upsert_wh = text("""
                    INSERT INTO warehouse_stats (warehouse_id, delivered_at, total_revenue, package_count)
                    VALUES (:wid, :dat, :rev, :pkg)
                    ON DUPLICATE KEY UPDATE 
                        total_revenue = VALUES(total_revenue),
                        package_count = VALUES(package_count)
                """)
                main_db.execute(upsert_wh, {
                    "wid": row.warehouse_id,
                    "dat": row.del_date,
                    "rev": row.total_rev,
                    "pkg": row.pkg_count
                })
            
            main_db.commit()
            stats_log(f"Node [{node_key}]: Thành công ({len(product_rows)} SP, {len(warehouse_rows)} WH)")
            node_session.close()
            return len(product_rows), len(warehouse_rows)
        except Exception as e:
            raise e
