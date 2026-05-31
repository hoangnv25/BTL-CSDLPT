# KẾ HOẠCH TRIỂN KHAI HỆ THỐNG THỐNG KÊ (ANALYTICS ENGINE)
**Dự án:** Hệ thống Quản lý Phân tán (Distributed Warehouse Management)
**Trạng thái:** Đang triển khai (In Progress)

---

## 1. MỤC TIÊU
Xây dựng cơ chế thu thập và tổng hợp dữ liệu doanh số từ các Node (North, Central, South) để cung cấp các báo cáo hiệu năng cao:
- **Top sản phẩm bán chạy:** Tổng hợp số lượng sản phẩm hoàn thành giao hàng.
- **Thống kê doanh thu:** Tổng hợp dòng tiền thực tế dựa trên đơn đặt hàng.

---

## 2. KIẾN TRÚC DỮ LIỆU (PRE-AGGREGATION)
Để tối ưu hiệu năng và đảm bảo tính phân tán tuyệt đối, hệ thống sử dụng bảng thống kê tập hợp thay vì truy vấn trực tiếp bảng nghiệp vụ:

### 2.1. Model: `PackageSalesStat` (Tại mỗi Node nhánh)
- **Tên bảng:** `package_sales_stats`
- **Cột:** `product_id`, `warehouse_id`, `delivered_at`, `quantity`, `revenue`, `package_count`.
- **Cơ chế cập nhật:** 
    - Khi một kiện hàng chuyển sang `Delivered`, hệ thống sẽ cập nhật bảng này.
    - `package_count`: Chỉ tăng 1 đơn vị cho mỗi kiện hàng thành công (tránh đếm lặp khi kiện hàng có nhiều sản phẩm).
    - **Tối giản hóa:** Bảng `packages` gốc không còn lưu cột `delivered_at` để giảm dư thừa, mọi thông tin thời gian giao hàng được tập trung tại bảng stats.

---

## 3. CHI TIẾT 2 API CHÍNH

### API 1: Tìm Top Sản Phẩm Bán Chạy
... (Giữ nguyên luồng gọi song song) ...

### API 2: Thống Kê Doanh Thu và Tổng Kiện Hàng
- **Endpoint:** `GET /stats/revenue`
- **Cơ chế xử lý:**
    - **Tất cả số liệu đều lấy từ bảng stats:** Cả Doanh thu (`SUM(revenue)`) và Tổng kiện hàng (`SUM(package_count)`) đều được tính từ bảng `package_sales_stats`.
    - **Hiệu năng:** Tốc độ phản hồi cực nhanh vì bảng stats đã được thu gọn (theo ngày/sản phẩm/kho) thay vì quét hàng triệu dòng kiện hàng.

---

## 4. DANH SÁCH CÁC CÔNG VIỆC (TODO)

### Giai đoạn 1: Thiết lập nền tảng 
- [x] Tạo Model `ProductSalesStat`.
- [x] Cấu hình `main.py` để tự động tạo bảng này trên các Node phụ.
- [x] Triển khai cơ chế Đổi tên cột `sale_date` -> `delivered_at` và vá dữ liệu cũ.

### Giai đoạn 2: Thu thập và Vá dữ liệu
- [x] Tích hợp logic update stats (bao gồm doanh thu) vào `PackageService`.
- [x] Tự động tính toán lại doanh thu cho các dữ liệu cũ bị thiếu (Vá dữ liệu tại `main.py`).

### Giai đoạn 3: Hoàn thiện Dashboard & UI
- [x] Đồng bộ bộ lọc (Ngày/Tháng/Năm) giữa Frontend và Backend.
- [x] Hiển thị "Tổng Doanh Thu" và "Tổng Kiện Hàng" chính xác trên UI.
- [x] Xử lý fallback `delivered_at` về `created_at` cho các đơn hàng cũ chưa có ngày giao.

---

## 5. HƯỚNG DẪN KIỂM TRA (FOR DEVS)
1. **Kiểm tra bảng:** Dùng công cụ SQL xem tại các Node (3307, 3308, 3309) đã có bảng `product_sales_stats` chưa.
2. **Kích hoạt dữ liệu:** Cập nhật 1 kiện hàng sang `Delivered` qua API `/package/{id}/status`.
3. **Gọi API:** Sử dụng Swagger UI (`/docs`) để test các endpoint trong mục **Statistics**.
