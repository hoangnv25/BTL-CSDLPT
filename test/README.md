# Hướng Dẫn So Sánh Hiệu Năng: CSDL Tập Trung (Centralized) vs Phân Tán (Distributed)

Thư mục này chứa các kịch bản kiểm thử tải (load testing) bằng **k6** nhằm so sánh trực quan hiệu năng và khả năng chịu tải của API lấy thông tin sản phẩm (`GET /product`) dưới hai mô hình cấu hình cơ sở dữ liệu.

---

## 1. Các File Trong Thư Mục
* **`README.md`**: File hướng dẫn này.
* **`benchmark_product.js`**: Script k6 mô phỏng lượng người dùng tăng dần từ 30 $\rightarrow$ 90 $\rightarrow$ 150 VUs trong thời gian ngắn (5s mỗi stage, tổng 20s).
* **`compare.py`**: Script Python tự động phân tích các file kết quả JSON xuất ra từ k6 và in bảng tổng hợp so sánh trực quan định dạng Markdown.

---

## 2. Cách Chạy Test Tự Động (Khuyên Dùng - 1 Lệnh Duy Nhất)

Để tiện lợi và không phải gõ nhiều lệnh thủ công, bạn chỉ cần đứng ở thư mục gốc của dự án (`d:\17._Ki_6\BTL CSDL PT\csdlpt`) và chạy lệnh Python duy nhất dưới đây:

```powershell
python test/run_benchmarks.py
```

**Script tự động này sẽ:**
1. Chạy kịch bản test **Tập trung** (Lưu kết quả vào `centralized_summary.json`).
2. Chạy kịch bản test **Phân tán** (Lưu kết quả vào `distributed_summary.json`).
3. Tắt `mysql_node1` thông qua Docker Compose $\rightarrow$ Chạy kịch bản test **Failover** (Lưu kết quả vào `distributed_failover_summary.json`).
4. Khởi động lại `mysql_node1` (Đảm bảo dọn dẹp và khôi phục hệ thống an toàn).
5. Tự động gọi `compare.py` để biên dịch bảng so sánh kết quả ra file `test/comparison_result.md`.

---

## 3. Cách Chạy Thủ Công Từng Bước (Nếu Muốn)

Nếu muốn chạy riêng từng kịch bản hoặc chạy thủ công từng bước:

* **Bước 1: Chạy test mô hình Tập trung (Centralized)**
  ```powershell
  & "C:\Program Files\k6\k6.exe" run -e TARGET_NODE=main --summary-export=test/centralized_summary.json test/benchmark_product.js
  ```
* **Bước 2: Chạy test mô hình Phân tán (Distributed)**
  ```powershell
  & "C:\Program Files\k6\k6.exe" run -e TARGET_NODE=auto --summary-export=test/distributed_summary.json test/benchmark_product.js
  ```
* **Bước 3: Chạy test Phân tán khi sập 1 chi nhánh (Failover)**
  1. Tắt Node 1:
     ```powershell
     docker compose stop mysql_node1
     ```
  2. Chạy test:
     ```powershell
     & "C:\Program Files\k6\k6.exe" run -e TARGET_NODE=auto --summary-export=test/distributed_failover_summary.json test/benchmark_product.js
     ```
  3. Bật lại Node 1:
     ```powershell
     docker compose start mysql_node1
     ```

---

## 4. Tổng Hợp & So Sánh Kết Quả

Sau khi chạy xong các lệnh trên, bạn sẽ có các file `centralized_summary.json`, `distributed_summary.json`, và `distributed_failover_summary.json` trong thư mục `test/`.

Hãy chạy script Python để tự động tổng hợp kết quả thành bảng Markdown:
```powershell
python test/compare.py
```
Bảng kết quả sẽ hiển thị chi tiết các thông số:
* **Tổng số Request xử lý** (nhiều hơn tức là throughput tốt hơn).
* **Throughput (req/s)**.
* **Thời gian phản hồi** (Average Latency, P90, P95).
* **Tỷ lệ lỗi (Error %)**.
