from datetime import datetime
import logging
from sqlalchemy import inspect, text
from BE.database import engines, circuit_breaker

logger = logging.getLogger("app")

def migration_log(content: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{time_str}] [Migration] {content}"
    print(log_line, flush=True)
    logger.info(log_line)


def migrate_main_inventories_to_shards():
    migration_log("Bắt đầu kiểm tra di trú dữ liệu tồn kho từ main DB...")
    if "main" not in engines:
        migration_log("Không tìm thấy kết nối đến main DB. Hủy di trú.")
        return

    main_engine = engines["main"]
    inspector = inspect(main_engine)
    
    # Kiểm tra xem bảng 'inventories' có tồn tại ở main DB hay không
    if "inventories" not in inspector.get_table_names():
        migration_log("Bảng 'inventories' không tồn tại trên main DB. Không cần thực hiện di trú.")
        return

    migration_log("Phát hiện bảng 'inventories' trên main DB. Bắt đầu quá trình di trú dữ liệu phân tán...")

    # Đọc dữ liệu inventories từ main DB
    with main_engine.connect() as main_conn:
        try:
            inventories = main_conn.execute(text("SELECT id, product_id, warehouse_id, stock_quantity, updated_at FROM inventories")).all()
            migration_log(f"Đọc thành công {len(inventories)} bản ghi tồn kho từ main DB.")
            
            # Đọc danh sách warehouses để xác định region
            warehouses_raw = main_conn.execute(text("SELECT id, region FROM warehouses")).all()
            warehouse_regions = {w[0]: w[1] for w in warehouses_raw}
            migration_log(f"Đọc thông tin {len(warehouse_regions)} kho hàng từ main DB để ánh xạ vùng miền.")
        except Exception as e:
            migration_log(f"LỖI: Không thể đọc dữ liệu tồn kho hoặc kho hàng từ main DB: {e}")
            return

        # Sắp xếp và chuyển dữ liệu sang các Node phụ tương ứng
        node_records = {"north": [], "central": [], "south": []}
        
        for inv in inventories:
            inv_id, product_id, warehouse_id, stock_quantity, updated_at = inv
            region = warehouse_regions.get(warehouse_id)
            if not region:
                migration_log(f"CẢNH BÁO: Không tìm thấy kho hàng (warehouse_id={warehouse_id}) cho bản ghi tồn kho ID={inv_id}. Bỏ qua bản ghi này.")
                continue
            
            # Map region string/enum to database node key
            node_key = None
            if region in ["North", "RegionEnum.North"]:
                node_key = "north"
            elif region in ["Central", "RegionEnum.Central"]:
                node_key = "central"
            elif region in ["South", "RegionEnum.South"]:
                node_key = "south"
            else:
                migration_log(f"CẢNH BÁO: Vùng miền '{region}' không hợp lệ cho kho hàng {warehouse_id}. Bỏ qua.")
                continue

            node_records[node_key].append({
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "stock_quantity": stock_quantity,
                "updated_at": updated_at
            })

        migration_log("Bắt đầu ghi dữ liệu tồn kho sang các Node phụ phân sharding...")

        # Thực hiện chèn dữ liệu sang các Node phụ
        for node_key, records in node_records.items():
            if not records:
                continue
            
            if node_key not in engines:
                migration_log(f"LỖI: Không cấu hình kết nối cho Node phụ '{node_key}'. Không thể di trú {len(records)} bản ghi.")
                continue
            
            node_engine = engines[node_key]
            migration_log(f"Đang ghi {len(records)} bản ghi tồn kho vào Node phụ phân mảnh: [{node_key}]...")

            with node_engine.begin() as node_conn:
                try:
                    # Tắt kiểm tra khóa ngoại để tránh lỗi do thứ tự đồng bộ
                    node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                    
                    for r in records:
                        # Kiểm tra xem bản ghi đã tồn tại chưa để tránh trùng lặp
                        exists = node_conn.execute(
                            text("SELECT 1 FROM inventories WHERE product_id = :product_id AND warehouse_id = :warehouse_id"),
                            {"product_id": r["product_id"], "warehouse_id": r["warehouse_id"]}
                        ).first()
                        
                        if not exists:
                            node_conn.execute(
                                text("""
                                    INSERT INTO inventories (product_id, warehouse_id, stock_quantity, updated_at)
                                    VALUES (:product_id, :warehouse_id, :stock_quantity, :updated_at)
                                """),
                                r
                            )
                    
                    # Bật lại kiểm tra khóa ngoại
                    node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    migration_log(f"Ghi thành công dữ liệu tồn kho vào Node phụ: [{node_key}].")
                except Exception as e:
                    migration_log(f"LỖI nghiêm trọng khi ghi dữ liệu vào Node phụ [{node_key}]: {e}")
                    try:
                        node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    except:
                        pass
                    raise e

        # Xóa bảng cũ ở main DB
        migration_log("Tất cả dữ liệu đã được sao chép thành công. Đang dọn dẹp bảng 'inventories' trên main DB...")
        try:
            main_conn.execute(text("DROP TABLE inventories;"))
            migration_log("Đã DROP bảng 'inventories' trên main DB thành công. Hoàn tất quá trình di trú tồn kho.")
        except Exception as e:
            migration_log(f"CẢNH BÁO: Di trú thành công nhưng không thể DROP bảng 'inventories' trên main DB: {e}")


def verify_and_initialize_missing_inventories():
    migration_log("Bắt đầu kiểm tra và bù đắp các bản ghi tồn kho còn thiếu trên toàn hệ thống phân tán...")
    
    if "main" not in engines:
        migration_log("Không tìm thấy kết nối đến main DB. Bỏ qua kiểm tra bù đắp.")
        return

    main_engine = engines["main"]
    
    try:
        # Lấy danh sách toàn bộ sản phẩm (kể cả sản phẩm bị xóa mềm) và kho hàng từ main DB
        with main_engine.connect() as main_conn:
            products = main_conn.execute(text("SELECT id, name, category_id, price, deleted_at FROM products")).all()
            warehouses = main_conn.execute(text("SELECT id, name, region FROM warehouses")).all()
            
        migration_log(f"Tìm thấy {len(products)} sản phẩm và {len(warehouses)} kho hàng trên main DB để đối chiếu.")
    except Exception as e:
        migration_log(f"LỖI: Không thể đọc danh sách sản phẩm hoặc kho hàng từ main DB: {e}")
        return

    # Gom nhóm các kho hàng theo node phân mảnh tương ứng
    node_warehouses = {"north": [], "central": [], "south": []}
    for wh in warehouses:
        wh_id, wh_name, region = wh
        node_key = None
        if region in ["North", "RegionEnum.North"]:
            node_key = "north"
        elif region in ["Central", "RegionEnum.Central"]:
            node_key = "central"
        elif region in ["South", "RegionEnum.South"]:
            node_key = "south"
            
        if node_key and node_key in engines:
            node_warehouses[node_key].append(wh)

    def sync_single_node(node: str, wh_list: list) -> bool:
        if not circuit_breaker.is_available(node):
            migration_log(f"Circuit Breaker: Bỏ qua Node [{node}] do đang ở trạng thái OFFLINE.")
            return False
            
        if not wh_list:
            return True
            
        node_engine = engines[node]
        try:
            # Kiểm tra kết nối trước
            with node_engine.connect():
                pass
        except Exception as e:
            circuit_breaker.mark_failure(node)
            migration_log(f"LỖI: Không thể kết nối tới Node [{node}] để bù đắp: {e}")
            return False

        try:
            with node_engine.begin() as node_conn:
                for wh in wh_list:
                    wh_id, wh_name, region = wh
                    # Lấy danh sách inventory hiện có trên node phụ này cho kho hàng wh_id
                    existing_product_ids = {
                        row[0] for row in node_conn.execute(
                            text("SELECT product_id FROM inventories WHERE warehouse_id = :warehouse_id"),
                            {"warehouse_id": wh_id}
                        ).all()
                    }
                    
                    # Check từng sản phẩm
                    for prod in products:
                        p_id, p_name, cat_id, price, p_deleted_at = prod
                        if p_id not in existing_product_ids:
                            status_str = "xóa mềm" if p_deleted_at else "hoạt động"
                            migration_log(
                                f"Phát hiện THIẾU tồn kho cho sản phẩm {status_str} '{p_name}' (ID={p_id}) tại kho '{wh_name}' (ID={wh_id}) trên Node phụ [{node}]"
                            )
                            
                            # Tắt kiểm tra khóa ngoại tạm thời để bảo đảm an toàn khi bù đắp dữ liệu
                            node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                            
                            # 1. Đảm bảo sản phẩm tồn tại cục bộ trên Node phụ này để không vi phạm khóa ngoại
                            prod_exists = node_conn.execute(
                                text("SELECT 1 FROM products WHERE id = :id"),
                                {"id": p_id}
                            ).first()
                            
                            if not prod_exists:
                                migration_log(f"-> Đang chèn bù đồng bộ sản phẩm {status_str} '{p_name}' (ID={p_id}) sang Node [{node}]...")
                                node_conn.execute(
                                    text("""
                                        INSERT INTO products (id, name, category_id, price, deleted_at)
                                        VALUES (:id, :name, :category_id, :price, :deleted_at)
                                    """),
                                    {"id": p_id, "name": p_name, "category_id": cat_id, "price": price, "deleted_at": p_deleted_at}
                                )
                            
                            # 2. Tạo bản ghi tồn kho mặc định
                            migration_log(f"-> Khởi tạo dòng tồn kho mặc định (quantity=0) tại Node [{node}]")
                            node_conn.execute(
                                text("""
                                    INSERT INTO inventories (product_id, warehouse_id, stock_quantity, updated_at)
                                    VALUES (:product_id, :warehouse_id, 0, NOW())
                                """),
                                {"product_id": p_id, "warehouse_id": wh_id}
                            )
                            
                            # Bật lại kiểm tra khóa ngoại
                            node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            circuit_breaker.mark_success(node)
            return True
        except Exception as e:
            circuit_breaker.mark_failure(node)
            migration_log(f"LỖI nghiêm trọng khi chạy bù đắp trên Node phụ [{node}]: {e}")
            return False

    # Chạy song song quá trình đối chiếu cho 3 node với giới hạn thời gian chờ 0.5 giây
    from concurrent.futures import ThreadPoolExecutor, wait
    migration_pool = ThreadPoolExecutor(max_workers=3)
    
    futures = {migration_pool.submit(sync_single_node, node, wh_list): node for node, wh_list in node_warehouses.items() if wh_list}
    done, not_done = wait(futures.keys(), timeout=0.5)
    
    for f in done:
        node = futures[f]
        try:
            success = f.result()
            if success:
                migration_log(f"Hoàn tất kiểm tra đối chiếu và bù đắp tồn kho phân tán cho Node: [{node}]")
        except Exception as e:
            migration_log(f"LỖI không mong đợi khi xử lý luồng bù đắp cho Node [{node}]: {e}")
            
    for f in not_done:
        node = futures[f]
        circuit_breaker.mark_failure(node)
        migration_log(f"TIMEOUT: Quá trình bù đắp tồn kho trên Node [{node}] không hoàn thành trong 0.5s. Đánh dấu OFFLINE.")

    migration_log("Hoàn tất kiểm tra đối chiếu và bù đắp tồn kho phân tán.")
