# KẾ HOẠCH TRIỂN KHAI HỆ THỐNG THỐNG KÊ (ANALYTICS ENGINE)
**Dự án:** Hệ thống Quản lý Phân tán (Distributed Warehouse Management)
**Trạng thái:** Đang triển khai (In Progress)

---

## 1. MỤC TIÊU
Xây dựng cơ chế thu thập và tổng hợp dữ liệu doanh số từ các Node (North, Central, South) để cung cấp các báo cáo hiệu năng cao:
- **Top sản phẩm bán chạy:** Tổng hợp số lượng sản phẩm hoàn thành giao hàng.
- **Thống kê doanh thu:** Tổng hợp dòng tiền thực tế dựa trên đơn đặt hàng.

---

## 2. KIẾN TRÚC DỮ LIỆU (CENTRALIZED PERIODIC AGGREGATION)
Hệ thống chuyển từ cơ chế cập nhật Real-time tại Node sang cơ chế **Tổng hợp định kỳ về DB Tập trung**:

### 2.1. Model: `PackageSalesStat` (Tại DB Trung tâm)
- **Tên bảng:** `package_sales_stats`
- **Vị trí:** Lưu trữ tại **Main Database (Trung tâm)** thay vì các Node nhánh.
- **Cột:** `product_id`, `warehouse_id`, `delivered_at`, `quantity`, `revenue`, `package_count`.
- **Cơ chế cập nhật (Chạy lúc 1:00 AM hàng ngày):** 
    - Hệ thống quét tất cả các Node (North, Central, South).
    - Truy vấn trực tiếp các kiện hàng có trạng thái `Delivered` từ bảng `packages` và `package_details`.
    - Tổng hợp theo ngày và sản phẩm, sau đó "Upsert" (Insert hoặc Update) vào bảng thống kê tại Main DB.

---

## 3. CHI TIẾT CÁC API

### API 1: Tìm Top Sản Phẩm Bán Chạy
- **Cơ chế:** Truy vấn trực tiếp từ bảng `package_sales_stats` tại Main DB. Không còn gọi song song tới các Node khi người dùng xem báo cáo, giúp giảm tải cho các Node và tăng tốc độ phản hồi.

### API 2: Thống Kê Doanh Thu và Tổng Kiện Hàng
- **Endpoint:** `GET /stats/revenue`
- **Cơ chế:** 
    - Tính toán `SUM(revenue)` và `SUM(package_count)` từ bảng thống kê tập trung.
    - Hỗ trợ bộ lọc theo Kho, Ngày, Tháng, Năm linh hoạt.

---

## 4. DANH SÁCH CÁC CÔNG VIỆC (UPDATED)

### Giai đoạn 1: Chuyển đổi sang DB Tập trung
- [x] Di chuyển Model `PackageSalesStat` vào Main DB.
- [x] Triển khai hàm `sync_all_stats_to_central()` trong `StatsService`.
- [x] Thiết lập `lifespan` trong `main.py` để chạy background task đồng bộ lúc 1:00 AM.

### Giai đoạn 2: Tối ưu hóa Node
- [x] Loại bỏ logic `update_stats` Real-time trong `PackageService` tại các Node.
- [x] Chuyển các API thống kê sang đọc dữ liệu từ Main DB.

### Giai đoạn 3: Kiểm trì và Vá dữ liệu
- [ ] Chạy lần đồng bộ đầu tiên để vá dữ liệu lịch sử về Main DB.
- [ ] Kiểm tra tính chính xác của dữ liệu sau khi tổng hợp.

---

## 5. HƯỚNG DẪN KIỂM TRA (FOR DEVS)
1. **Kiểm tra bảng:** Dùng công cụ SQL xem tại các Node (3307, 3308, 3309) đã có bảng `product_sales_stats` chưa.
2. **Kích hoạt dữ liệu:** Cập nhật 1 kiện hàng sang `Delivered` qua API `/package/{id}/status`.
3. **Gọi API:** Sử dụng Swagger UI (`/docs`) để test các endpoint trong mục **Statistics**.
