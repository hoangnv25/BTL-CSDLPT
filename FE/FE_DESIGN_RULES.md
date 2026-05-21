# QUY ĐỊNH THIẾT KẾ VÀ GIAO DIỆN (FE DESIGN & STYLING RULES)
> Định nghĩa phong cách thiết kế UI/UX (Dựa trên DeepCulture Admin / Linear-inspired) rút gọn dành cho AI. Đọc và tuân thủ nghiêm ngặt.

---

## 1. Màu Sắc & Kiểu Chữ (Variables)
Sử dụng các CSS variables sau để đảm bảo giao diện sạch sẽ, tối giản và tập trung vào nội dung:
```css
:root {
  --font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;
  
  /* Primary Colors */
  --primary-color: #9a2e24; /* Đỏ sẫm truyền thống */
  --primary-hover: #7a241c; 
  
  /* Backgrounds */
  --bg-main: #ffffff;
  --bg-sidebar: #ffffff;
  --surface-hover: #f9f9f9;
  
  /* Text & Border */
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --border-color: #e5e5e5; /* Hoặc #f0f0f0 */
  
  /* Status Colors (nếu cần) */
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  
  --transition: all 0.2s ease-in-out;
}
```

---

## 2. Typography & Khoảng Trắng (Whitespace)
* **Font chữ**: Bắt buộc dùng `Be Vietnam Pro` (Ưu tiên từ Google Fonts).
* **Trọng số (Weights)**:
  - `400` (Regular): Nội dung văn bản thường.
  - `500` (Medium): Nhãn, nút bấm.
  - `600` (SemiBold): Tiêu đề nhỏ, header của bảng.
  - `700` (Bold): Tiêu đề trang, tiêu đề quan trọng.
* **Kích thước**: Base font `14px` cho admin, tiêu đề từ `18px - 24px`.
* **Khoảng trắng**: Sử dụng khoảng trắng rộng rãi để phân tách các khu vực chức năng, tránh cảm giác chật chội. Mọi pixel đều phải có ý nghĩa (Sạch sẽ - Clean).
* **Độ tương phản**: Đảm bảo text trên nền trắng rõ ràng, dễ đọc cho việc quản trị dữ liệu lâu dài.

---

## 3. Phong Cách Component (Linear Inspired)
* **Thẻ (Tags/Badges)**: Padding nhỏ (`2px 8px`), bo góc nhẹ (`4px`). Border mỏng `1px`, nền nhạt hơn text. Viết chữ thường với font-weight `500` hoặc viết hoa nhẹ.
* **Nút bấm (Buttons)**: 
  - Chiều cao chuẩn (`32px - 36px` cho admin).
  - Bo góc `4px - 6px` (không bo tròn hoàn toàn).
  - Hiệu ứng hover: Làm đậm màu hoặc thêm shadow nhẹ.
* **Bảng (Tables)**: 
  - Tiêu đề cột (Header): font-size nhỏ hơn, màu xám nhạt (`--text-secondary`), font-weight `600`.
  - Khung: KHÔNG kẻ khung dọc, chỉ kẻ ngang rất mỏng giữa các hàng (`border-bottom: 1px solid var(--border-color)`).
  - Hover hàng: Đổi màu nền sang `--surface-hover` (`#f9f9f9`).
* **Input/Forms**: 
  - Border `--border-color` (`#e5e5e5`).
  - Khi focus: đổi sang màu `--primary-color` (`#9a2e24`) với shadow nhẹ.

---

## 4. Ant Design & Thư Viện Hỗ Trợ
* **Ant Design (`antd`)**: 
  - CHỈ dùng cho toast/feedback ngắn qua `message` (VD: `message.success(...)`, `message.error(...)`).
  - KHÔNG bọc root bằng `ConfigProvider`/`App` chỉ để dùng message.
  - KHÔNG dùng các component UI khác của Antd (`Table`, `Modal`, `Form`, `Input`, `Select`, `Pagination`) trong module CRUD hiện tại.
* **Thông báo lỗi/nghiệp vụ**:
  - KHÔNG dùng `window.alert` cho thông báo nghiệp vụ thông thường.
  - Lỗi cần giữ trên màn hình (để đọc hoặc sửa form) thì hiển thị alert inline trong layout (vd: chữ đỏ dưới ô input form).
* **UI Bảng, Form, Modal**: Ưu tiên component tự viết + CSS Modules để giữ đúng thiết kế Minimalist của DeepCulture.
* **Icons**: Bắt buộc sử dụng `@phosphor-icons/react` để đồng bộ style sidebar và action của bảng.

---

## 5. Phân Trang (Pagination) & Thanh Cuộn (Scrollbar)
* **Client-side Pagination**: Vì Backend trả về toàn bộ dữ liệu (không hỗ trợ `limit`/`offset`), mọi bảng danh sách (Table) có nguy cơ chứa lượng dữ liệu lớn đều phải **tự cắt dữ liệu hiển thị ở Client**.
  - Giới hạn: **10 dòng / 1 trang**.
  - Reset `currentPage` về `1` mỗi khi fetch API hoặc thay đổi điều kiện Lọc (Filter).
* **Thiết kế Thanh Phân Trang (Pagination Bar)**:
  - Vị trí: Dưới cùng của bảng (`.pagination`), thiết kế dạt sang phải, có dòng thông tin tóm tắt bên trái (vd: *Hiển thị 1 - 10 trong tổng số...*).
  - Nút chuyển trang (`.pageBtn`): Nền trắng/trong, viền xám mỏng, hover màu xám nhạt (`--surface-hover`).
  - Nút trang hiện tại (`.pageBtnActive`): Nền màu đỏ sẫm (`--primary-color`), chữ trắng.
* **Thanh Cuộn & Tiêu đề cố định (Scrollbar & Sticky Header)**:
  - Bảng phải luôn được bọc trong một `.tableContainer` có giới hạn chiều cao tối đa (`max-height: calc(100vh - 250px)`) và cho phép cuộn dọc (`overflow-y: auto`).
  - Cột tiêu đề (`th`) bắt buộc phải có thuộc tính `position: sticky; top: 0; z-index: 1` để giữ nguyên vị trí khi người dùng cuộn xem các dòng bên dưới.
