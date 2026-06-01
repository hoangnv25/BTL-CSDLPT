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
            
            # Đọc danh sách kho hàng từ các Node chi nhánh để xác định region
            warehouses_raw = []
            for node in ["north", "central", "south"]:
                if not circuit_breaker.is_available(node):
                    continue
                try:
                    with engines[node].connect() as node_conn:
                        whs = node_conn.execute(text("SELECT id, region FROM warehouses")).all()
                        warehouses_raw.extend(whs)
                except Exception as e:
                    migration_log(f"Cảnh báo: Không thể đọc kho hàng từ Node phụ [{node}] khi di trú inventories: {e}")
            warehouse_regions = {w[0]: w[1] for w in warehouses_raw}
            migration_log(f"Đọc thông tin {len(warehouse_regions)} kho hàng từ các Node chi nhánh để ánh xạ vùng miền.")
        except Exception as e:
            migration_log(f"LỖI: Không thể đọc dữ liệu tồn kho từ main DB hoặc kho từ các node: {e}")
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
        # Lấy danh sách toàn bộ sản phẩm (kể cả sản phẩm bị xóa mềm) từ main DB
        with main_engine.connect() as main_conn:
            products = main_conn.execute(text("SELECT id, name, category_id, price, deleted_at FROM products")).all()
            
        # Lấy danh sách kho hàng bằng cách gộp từ các Node phụ
        warehouses = []
        for node in ["north", "central", "south"]:
            if not circuit_breaker.is_available(node):
                continue
            try:
                with engines[node].connect() as node_conn:
                    whs = node_conn.execute(text("SELECT id, name, region FROM warehouses")).all()
                    warehouses.extend(whs)
            except Exception as e:
                migration_log(f"Cảnh báo: Không thể đọc kho hàng từ Node phụ [{node}] để bù đắp: {e}")
            
        migration_log(f"Tìm thấy {len(products)} sản phẩm trên main DB và {len(warehouses)} kho hàng gộp từ các Node phụ để đối chiếu.")
    except Exception as e:
        migration_log(f"LỖI: Không thể đọc danh sách sản phẩm từ main DB hoặc kho hàng từ các node: {e}")
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


def migrate_main_packages_to_shards():
    migration_log("Bắt đầu kiểm tra di trú dữ liệu kiện hàng từ main DB...")
    if "main" not in engines:
        migration_log("Không tìm thấy kết nối đến main DB. Hủy di trú.")
        return

    main_engine = engines["main"]
    inspector = inspect(main_engine)
    
    # Kiểm tra xem bảng 'packages' có tồn tại ở main DB hay không
    if "packages" not in inspector.get_table_names():
        migration_log("Bảng 'packages' không tồn tại trên main DB. Không cần thực hiện di trú.")
        return

    migration_log("Phát hiện bảng 'packages' trên main DB. Bắt đầu quá trình di trú...")

    with main_engine.connect() as main_conn:
        try:
            packages = main_conn.execute(text("SELECT id, order_id, warehouse_id, status, created_at FROM packages")).all()
            migration_log(f"Đọc thành công {len(packages)} bản ghi kiện hàng từ main DB.")
            
            # Đọc chi tiết kiện hàng
            package_details = []
            if "package_details" in inspector.get_table_names():
                package_details = main_conn.execute(text("SELECT id, package_id, product_id, quantity FROM package_details")).all()
                migration_log(f"Đọc thành công {len(package_details)} chi tiết kiện hàng từ main DB.")

            # Đọc danh sách kho hàng từ các Node chi nhánh để định tuyến
            warehouses_raw = []
            for node in ["north", "central", "south"]:
                if not circuit_breaker.is_available(node):
                    continue
                try:
                    with engines[node].connect() as node_conn:
                        whs = node_conn.execute(text("SELECT id, region FROM warehouses")).all()
                        warehouses_raw.extend(whs)
                except Exception as e:
                    migration_log(f"Cảnh báo: Không thể đọc kho hàng từ Node phụ [{node}] khi di trú packages: {e}")
            warehouse_regions = {w[0]: w[1] for w in warehouses_raw}
        except Exception as e:
            migration_log(f"LỖI: Không thể đọc dữ liệu kiện hàng từ main DB hoặc kho từ các node: {e}")
            return

        # Phân loại kiện hàng và chi tiết kiện hàng theo Node
        node_packages = {"north": [], "central": [], "south": []}
        package_id_to_node = {}

        for pkg in packages:
            pkg_id, order_id, warehouse_id, status, created_at = pkg
            region = warehouse_regions.get(warehouse_id)
            if not region:
                migration_log(f"CẢNH BÁO: Không tìm thấy kho hàng (warehouse_id={warehouse_id}) cho kiện hàng ID={pkg_id}. Bỏ qua.")
                continue
            
            node_key = None
            if region in ["North", "RegionEnum.North"]:
                node_key = "north"
            elif region in ["Central", "RegionEnum.Central"]:
                node_key = "central"
            elif region in ["South", "RegionEnum.South"]:
                node_key = "south"
            else:
                migration_log(f"CẢNH BÁO: Vùng miền '{region}' không hợp lệ cho kho {warehouse_id}. Bỏ qua.")
                continue
            
            package_id_to_node[pkg_id] = node_key
            node_packages[node_key].append({
                "id": pkg_id,
                "order_id": order_id,
                "warehouse_id": warehouse_id,
                "status": status,
                "created_at": created_at,
                "details": []
            })

        for detail in package_details:
            dt_id, package_id, product_id, quantity = detail
            node_key = package_id_to_node.get(package_id)
            if not node_key:
                migration_log(f"CẢNH BÁO: Chi tiết kiện hàng ID={dt_id} trỏ đến package_id={package_id} không hợp lệ. Bỏ qua.")
                continue
            
            for p in node_packages[node_key]:
                if p["id"] == package_id:
                    p["details"].append({
                        "id": dt_id,
                        "package_id": package_id,
                        "product_id": product_id,
                        "quantity": quantity
                    })
                    break

        # Ghi vào các Node phụ
        for node_key, pkgs in node_packages.items():
            if not pkgs:
                continue
            
            if node_key not in engines:
                migration_log(f"LỖI: Không cấu hình kết nối cho Node phụ '{node_key}'. Không thể di trú {len(pkgs)} kiện hàng.")
                continue
            
            node_engine = engines[node_key]
            migration_log(f"Đang ghi {len(pkgs)} kiện hàng vào Node phụ phân mảnh: [{node_key}]...")

            with node_engine.begin() as node_conn:
                try:
                    node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                    
                    for p in pkgs:
                        exists = node_conn.execute(
                            text("SELECT 1 FROM packages WHERE id = :id"),
                            {"id": p["id"]}
                        ).first()
                        
                        if not exists:
                            node_conn.execute(
                                text("""
                                    INSERT INTO packages (id, order_id, warehouse_id, status, created_at)
                                    VALUES (:id, :order_id, :warehouse_id, :status, :created_at)
                                """),
                                {
                                    "id": p["id"],
                                    "order_id": p["order_id"],
                                    "warehouse_id": p["warehouse_id"],
                                    "status": p["status"],
                                    "created_at": p["created_at"]
                                }
                            )

                        for d in p["details"]:
                            det_exists = node_conn.execute(
                                text("SELECT 1 FROM package_details WHERE id = :id"),
                                {"id": d["id"]}
                            ).first()
                            
                            if not det_exists:
                                node_conn.execute(
                                    text("""
                                        INSERT INTO package_details (id, package_id, product_id, quantity)
                                        VALUES (:id, :package_id, :product_id, :quantity)
                                    """),
                                    d
                                )
                    
                    node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    migration_log(f"Ghi thành công {len(pkgs)} kiện hàng vào Node phụ: [{node_key}].")
                except Exception as e:
                    migration_log(f"LỖI nghiêm trọng khi ghi kiện hàng vào Node phụ [{node_key}]: {e}")
                    try:
                        node_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                    except:
                        pass
                    raise e

        # Ghi bảng ánh xạ order_package_shards trên main DB
        migration_log("Đang tạo bảng ánh xạ order_package_shards trên main DB...")
        with main_engine.begin() as main_conn:
            try:
                for pkg_id, node_key in package_id_to_node.items():
                    order_id = next(p["order_id"] for node_list in node_packages.values() for p in node_list if p["id"] == pkg_id)
                    
                    exists = main_conn.execute(
                        text("SELECT 1 FROM order_package_shards WHERE package_id = :package_id"),
                        {"package_id": pkg_id}
                    ).first()
                    
                    if not exists:
                        main_conn.execute(
                            text("INSERT INTO order_package_shards (package_id, order_id, node_name) VALUES (:package_id, :order_id, :node_name)"),
                            {"package_id": pkg_id, "order_id": order_id, "node_name": node_key}
                        )
                migration_log("Đã cập nhật bảng ánh xạ order_package_shards trên main DB.")
            except Exception as e:
                migration_log(f"LỖI khi tạo bảng ánh xạ order_package_shards: {e}")
                raise e

        # Dọn dẹp tables trên main DB
        migration_log("Đang dọn dẹp các bảng packages và package_details trên main DB...")
        with main_engine.begin() as main_conn:
            try:
                main_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                main_conn.execute(text("DROP TABLE IF EXISTS package_details;"))
                main_conn.execute(text("DROP TABLE IF EXISTS packages;"))
                main_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                migration_log("Đã DROP bảng 'packages' và 'package_details' trên main DB thành công. Hoàn tất quá trình di trú.")
            except Exception as e:
                migration_log(f"CẢNH BÁO: Không thể DROP bảng packages/package_details trên main DB: {e}")


def migrate_warehouses_to_shards():
    """Di trú dữ liệu bảng warehouses từ Main DB sang các phân mảnh ngang nguyên thủy ở Node phụ"""
    from BE.database import engines, get_db_node
    from BE.models.warehouse import Warehouse, RegionEnum
    from sqlalchemy import text, inspect
    
    migration_log("Bắt đầu kiểm tra di trú dữ liệu bảng warehouses từ Main DB...")
    
    main_engine = engines.get("main")
    if not main_engine:
        migration_log("Không tìm thấy kết nối đến main DB. Hủy di trú.")
        return
        
    with main_engine.connect() as main_conn:
        try:
            inspector = inspect(main_engine)
            # Kiểm tra xem bảng warehouses ở Main DB có dữ liệu không
            # Nếu chưa có/trống, ta sẽ thu thập từ các node để phục hồi Catalog trung tâm
            if "warehouses" not in inspector.get_table_names():
                migration_log("Bảng warehouses chưa tồn tại ở Main DB. Sẽ được khởi tạo lại.")
                warehouses_raw = []
            else:
                warehouses_raw = main_conn.execute(text("SELECT id, name, region, address FROM warehouses")).all()
            
            if not warehouses_raw:
                migration_log("Bảng warehouses ở Main DB đang trống. Đang thu thập dữ liệu từ các Node phụ để phục hồi Central Catalog...")
                all_collected = []
                for node in ["north", "central", "south"]:
                    if circuit_breaker.is_available(node):
                        try:
                            with engines[node].connect() as node_conn:
                                node_whs = node_conn.execute(text("SELECT id, name, region, address FROM warehouses")).all()
                                all_collected.extend(node_whs)
                                for w in node_whs:
                                    main_conn.execute(
                                        text("INSERT IGNORE INTO warehouses (id, name, region, address) VALUES (:id, :name, :region, :address)"),
                                        {"id": w[0], "name": w[1], "region": w[2], "address": w[3]}
                                    )
                                main_conn.commit()
                        except Exception as e:
                            migration_log(f"Lỗi phục hồi kho hàng từ node {node}: {e}")
                migration_log(f"Đã phục hồi {len(all_collected)} kho hàng về Main DB (Central Catalog).")
                return # Đã có dữ liệu, không cần chạy phần di trú xuôi nữa
        except Exception as e:
            migration_log(f"Lỗi kiểm tra/phục hồi Catalog kho hàng ở Main DB: {e}")
            return
            
    migration_log(f"Bắt đầu đồng bộ xuôi {len(warehouses_raw)} kho hàng từ Catalog sang các Node phụ tương ứng...")
    
    # Đẩy dữ liệu về các Node phụ
    for wh in warehouses_raw:
        wh_id, name, region, address = wh
        node_key = None
        if "North" in str(region):
            node_key = "north"
        elif "Central" in str(region):
            node_key = "central"
        elif "South" in str(region):
            node_key = "south"
            
        if not node_key:
            migration_log(f"CẢNH BÁO: Region '{region}' không xác định cho kho {wh_id}. Bỏ qua.")
            continue
            
        node_session = get_db_node(node_key)
        try:
            # Kiểm tra xem kho đã tồn tại ở node phụ chưa
            exists = node_session.query(Warehouse).filter(Warehouse.id == wh_id).first()
            if not exists:
                enum_val = None
                if node_key == "north":
                    enum_val = RegionEnum.North
                elif node_key == "central":
                    enum_val = RegionEnum.Central
                elif node_key == "south":
                    enum_val = RegionEnum.South
                    
                new_wh = Warehouse(id=wh_id, name=name, region=enum_val, address=address)
                node_session.add(new_wh)
                node_session.commit()
                migration_log(f"Đã di trú Kho ID {wh_id} ({name}) -> Node: [{node_key}]")
        except Exception as e:
            migration_log(f"Lỗi di trú kho hàng {wh_id}: {e}")
            node_session.rollback()
        finally:
            node_session.close()
            
    migration_log("Hoàn tất đồng bộ dữ liệu kho hàng giữa Main và các Node chi nhánh.")


def setup_node_foreign_keys(site_name: str, db_engine):
    """Thiết lập khóa ngoại vật lý fk_inventories_warehouses và fk_packages_warehouses trên Node phụ"""
    migration_log(f"Đang kiểm tra/thiết lập khóa ngoại vật lý cho Node: [{site_name}]...")
    with db_engine.begin() as conn:
        # 1. Khóa ngoại cho inventories
        try:
            exists = conn.execute(text("""
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_schema = DATABASE() 
                  AND table_name = 'inventories' 
                  AND constraint_name = 'fk_inventories_warehouses'
            """)).first()
            if not exists:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                conn.execute(text("""
                    ALTER TABLE inventories 
                    ADD CONSTRAINT fk_inventories_warehouses 
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
                    ON DELETE RESTRICT ON UPDATE CASCADE;
                """))
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                migration_log(f"Đã tạo khóa ngoại fk_inventories_warehouses trên Node: [{site_name}]")
        except Exception as e:
            migration_log(f"CẢNH BÁO: Lỗi tạo khóa ngoại inventories trên Node [{site_name}]: {e}")
            try:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            except:
                pass

        # 2. Khóa ngoại cho packages
        try:
            exists = conn.execute(text("""
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_schema = DATABASE() 
                  AND table_name = 'packages' 
                  AND constraint_name = 'fk_packages_warehouses'
            """)).first()
            if not exists:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                conn.execute(text("""
                    ALTER TABLE packages 
                    ADD CONSTRAINT fk_packages_warehouses 
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
                    ON DELETE RESTRICT ON UPDATE CASCADE;
                """))
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                migration_log(f"Đã tạo khóa ngoại fk_packages_warehouses trên Node: [{site_name}]")
        except Exception as e:
            migration_log(f"CẢNH BÁO: Lỗi tạo khóa ngoại packages trên Node [{site_name}]: {e}")
            try:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            except:
                pass
