# TIÊU CHUẨN LẬP TRÌNH FRONTEND (FE CODING STANDARDS)
> Hướng dẫn phát triển ngắn gọn, xúc tích dành riêng cho AI. Đọc và tuân thủ nghiêm ngặt.

---

## 1. Nguồn Tham Chiếu Nghiệp Vụ & API (BẮT BUỘC)
* **API Endpoints & Models**: Chỉ tra cứu duy nhất tại file [openapi.json](file:///d:/Study/CSDLPT/BTL-CSDLPT/FE/openapi.json).
* **Nghiệp Vụ & Logic Bán Hàng**: Chỉ đọc, phân tích mã nguồn từ thư mục backend **`BE/`** trong cùng workspace (`BTL-CSDLPT/BE/`). Tuyệt đối không tự suy diễn hoặc đọc các tài liệu/nguồn bên ngoài khác.
---

## 2. Xác Thực Đơn Giản & LocalStorage
* **Màn hình Login**: Người dùng nhập username và ấn Đăng nhập -> Gọi `POST /user/login`.
* **LocalStorage**: Lưu kết quả trả về của API Login vào `localStorage` dưới key `currentUser`:
  ```javascript
  localStorage.setItem('currentUser', JSON.stringify({ id, username, full_name }));
  ```
* **Đăng xuất**: Xóa key `currentUser` khỏi `localStorage` và chuyển `activeTab` về màn Login.
* **Tạo đơn hàng**: Khi tạo đơn hàng (`POST /order`), bắt buộc lấy `user_id` từ `currentUser` trong `localStorage` để truyền vào request body.

---

## 3. Kiến Trúc Giao Diện & Thư Mục Tối Giản
* **Không Header, Không Common**: Giao diện chỉ gồm **Sidebar** (Trái - Điều khiển) và **Content Area / Context** (Phải - Hiển thị).
* **Không Thư Mục Dư Thừa**: Không được tạo thêm bất cứ folder nào cùng cấp với `src` hoặc các thư mục dùng chung bên ngoài ngoài cấu trúc tối giản dưới đây.
* **CSS Modules**: BẮT BUỘC dùng CSS Modules (`*.module.css`) cho từng trang và Sidebar để tránh xung đột style.
* **Quy tắc 1 Page - 1 CSS**: Mỗi trang là một thư mục riêng biệt. Thư mục này chỉ chứa **duy nhất 1 file CSS Module dùng chung** cho cả file page chính và toàn bộ các modal/sub-component con nằm trong thư mục trang đó.
* **Icons**: Chỉ được sử dụng duy nhất thư viện **Phosphor Icons** (`@phosphor-icons/react` hoặc tương đương).

### Chi Tiết Cấu Trúc Thư Mục (`FE/src/`)
```text
src/
├── components/
│   └── Sidebar/       # Chỉ chứa component Sidebar lớn dùng chung
│       ├── Sidebar.jsx
│       └── Sidebar.module.css
├── pages/             # Chỉ chứa các thư mục tương ứng với từng Tab giao diện
│   ├── Login/
│   │   ├── Login.jsx
│   │   └── Login.module.css
│   ├── Order/         # Tab quản lý và tạo đơn hàng
│   │   ├── Order.jsx
│   │   ├── CreateOrderModal.jsx  # Modal tạo đơn hàng mới
│   │   └── Order.module.css
│   ├── Product/       # Tab quản lý sản phẩm
│   │   ├── Product.jsx
│   │   ├── ProductModal.jsx      # Modal thêm/sửa sản phẩm
│   │   └── Product.module.css
│   ├── Category/      # Tab quản lý danh mục
│   │   ├── Category.jsx
│   │   └── Category.module.css
│   ├── Warehouse/     # Tab quản lý kho hàng
│   │   ├── Warehouse.jsx
│   │   └── Warehouse.module.css
│   └── Inventory/     # Tab quản lý tồn kho (stock)
│       ├── Inventory.jsx
│       └── Inventory.module.css
├── App.jsx            # Điều phối activeTab (ví dụ: 'login', 'order', 'product', 'category', 'warehouse', 'inventory')
├── main.jsx           # Điểm khởi chạy React
└── index.css          # CSS reset và biến màu toàn cục
```

---

## 4. Quy Chuẩn Đồng Bộ UI (Consistent UI Elements)
Các thành phần giao diện lặp đi lặp lại nhiều lần (Modal, Card, Tag/Badge, Table) phải có chung thiết kế, Spacing, độ bo góc và màu sắc trong CSS Module:
* **Modal**: Tất cả modal phải dùng chung cấu trúc overlay mờ, bo góc `16px`, nút "Đóng" ở góc trên bên phải sử dụng icon Phosphor, và các nút hành động nằm dưới cùng bên phải.
* **Card**: Bo góc `12px`, nền màu trắng mờ, có viền mờ `rgba(226, 232, 240, 0.8)`.
* **Tag / Badge**: Các nhãn trạng thái phải có cùng padding (`0.25rem 0.75rem`), bo góc `9999px` (viên thuốc) và màu chữ đậm hơn màu nền tương ứng.
* **Thông báo & Xác nhận (Notification & Confirmation)**: Tuyệt đối **KHÔNG** sử dụng `alert()` hoặc `window.confirm()` mặc định của trình duyệt để tránh làm giảm trải nghiệm người dùng. **BẮT BUỘC** sử dụng các API thông báo thẩm mỹ từ Ant Design như `message` để thông báo thành công/thất bại và `Modal.confirm` để hiển thị hộp thoại xác nhận thao tác.


---

## 5. Quy Trình Phát Triển 3 Bước (Lập Plan - Chốt - Làm)
AI bắt buộc phải tuân theo quy trình phát triển 3 bước nghiêm ngặt sau cho mỗi tính năng mới:
1. **Bước 1: Lập Plan (Kế hoạch)**: Trước khi thực hiện sửa đổi hay tạo file code, AI phải nghiên cứu API (`openapi.json`) và viết một bản kế hoạch triển khai chi tiết (`implementation_plan.md`).
2. **Bước 2: Chốt (Phê duyệt)**: AI gửi bản kế hoạch cho người dùng xem xét và chỉ được bắt đầu thực hiện khi người dùng đã duyệt/chốt kế hoạch rõ ràng.
3. **Bước 3: Làm (Thực thi & Kiểm thử)**: Thực thi theo kế hoạch đã chốt, đảm bảo cấu trúc thư mục tối giản, dùng CSS Modules, Phosphor Icons, đồng bộ giao diện và kiểm thử tính năng hoạt động đúng.

### Luồng Triển Khai Chi Tiết khi bắt đầu "Làm":
* **B1 (Đọc API)**: Xác định chính xác các trường dữ liệu và logic liên quan.
* **B2 (Tạo Thư Mục)**: Tạo thư mục trang mới `src/pages/PageName/` (gồm 1 JSX chính, các Modal, 1 CSS Module dùng chung).
* **B3 (Giao Diện & Icon)**: Xây dựng CSS module, chỉ dùng Phosphor Icons, đồng bộ UI.
* **B4 (State & API)**: Dùng `useState` và `useEffect` xử lý API & State.
* **B5 (Đấu Nối)**: Tích hợp tab mới vào `Sidebar` và điều hướng trong `App.jsx` thông qua `activeTab`.
