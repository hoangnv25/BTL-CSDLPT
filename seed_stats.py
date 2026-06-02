import random
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine, text
import os

# Cấu hình kết nối (Sử dụng service names trong Docker network)
MAIN_URL = "mysql+pymysql://user:123@mysql:3307/db"
NORTH_URL = "mysql+pymysql://user:123@mysql_node1:3308/db"
CENTRAL_URL = "mysql+pymysql://user:123@mysql_node2:3309/db"
SOUTH_URL = "mysql+pymysql://user:123@mysql_node3:3310/db"

engines = {
    "main": create_engine(MAIN_URL),
    "north": create_engine(NORTH_URL),
    "central": create_engine(CENTRAL_URL),
    "south": create_engine(SOUTH_URL)
}

# Dữ liệu hiện có
product_ids = [9, 10, 11, 12, 13, 14, 17, 18]
product_prices = {
    9: 100000.0, 10: 100000.0, 11: 100000.0, 12: 100000.0,
    13: 50.0, 14: 100000.0, 17: 1000.0, 18: 1000.0
}
warehouses = [
    {"id": 1, "region": "north"},
    {"id": 2, "region": "north"},
    {"id": 3, "region": "central"},
    {"id": 4, "region": "south"}
]

def seed():
    today = date.today()
    print(f"Bắt đầu seed dữ liệu cho 90 ngày gần nhất (từ {today - timedelta(days=90)} đến {today})")

    for i in range(90):
        current_date = today - timedelta(days=i)
        
        # 1. Tạo Stats trên các Node phụ
        for wh in warehouses:
            node = wh["region"]
            engine = engines[node]
            
            # Mỗi ngày mỗi kho bán được một vài sản phẩm ngẫu nhiên
            num_products_sold = random.randint(2, 6)
            sampled_products = random.sample(product_ids, num_products_sold)
            
            with engine.connect() as conn:
                for pid in sampled_products:
                    qty = random.randint(1, 20)
                    rev = qty * product_prices[pid]
                    
                    stmt = text("""
                        INSERT INTO product_stats (product_id, warehouse_id, delivered_at, quantity, revenue)
                        VALUES (:pid, :wh_id, :sdate, :qty, :rev)
                        ON DUPLICATE KEY UPDATE 
                            quantity = quantity + :qty,
                            revenue = revenue + :rev
                    """)
                    conn.execute(stmt, {"pid": pid, "wh_id": wh["id"], "sdate": current_date, "qty": qty, "rev": rev})
                conn.commit()

        # 2. Tạo Order trên Main DB
        with engines["main"].connect() as conn:
            num_orders = random.randint(5, 15)
            for _ in range(num_orders):
                total_amt = random.uniform(50000, 2000000)
                ordered_at = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=random.randint(8, 20))
                
                result = conn.execute(text("""
                    INSERT INTO orders (user_id, shipping_address, total_amount, ordered_at)
                    VALUES (1, 'Địa chỉ giả lập', :amt, :oat)
                """), {"amt": total_amt, "oat": ordered_at})
                order_id = result.lastrowid
                
                # 3. Tạo Kiện hàng (Package) tương ứng trên Node phụ ngẫu nhiên
                wh = random.choice(warehouses)
                node_engine = engines[wh["region"]]
                with node_engine.connect() as node_conn:
                    # Tạo Package với trạng thái Delivered để khớp với dữ liệu Stats
                    pkg_result = node_conn.execute(text("""
                        INSERT INTO packages (order_id, warehouse_id, status, created_at, delivered_at)
                        VALUES (:oid, :wid, 'Delivered', :cat, :cat)
                    """), {"oid": order_id, "wid": wh["id"], "cat": ordered_at})
                    pkg_id = pkg_result.lastrowid
                    
                    # Tạo Package Details
                    num_items = random.randint(1, 3)
                    sampled_items = random.sample(product_ids, num_items)
                    for pid in sampled_items:
                        qty = random.randint(1, 5)
                        node_conn.execute(text("""
                            INSERT INTO package_details (package_id, product_id, quantity)
                            VALUES (:pkid, :pid, :qty)
                        """), {"pkid": pkg_id, "pid": pid, "qty": qty})
                    node_conn.commit()
            conn.commit()
        
        if i % 10 == 0:
            print(f"Đã seed xong ngày {current_date}")

    print("Hoàn tất seed dữ liệu!")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"Lỗi khi seed: {e}")
