# Quy tắc Thiết kế (Design Rules) - DeepCulture Admin

Dưới đây là các quy tắc thiết kế bắt buộc cho giao diện quản trị DeepCulture, dựa trên phong cách tối giản, hiện đại của Linear và bảng màu đặc trưng.

## 1. Hệ thống Màu sắc (Color Palette)
- **Màu chủ đạo (Primary):** `#9a2e24` (Đỏ sẫm truyền thống). Sử dụng cho các nút hành động chính (Primary Buttons), Header, hoặc các điểm nhấn quan trọng.
- **Màu nền (Background):** `#ffffff` (Trắng). Giao diện cần sự sạch sẽ, tập trung vào nội dung.
- **Màu bổ trợ:**
  - Text: `#1a1a1a` (Đen gần tuyệt đối cho tiêu đề) và `#666666` (Xám cho nội dung phụ).
  - Border/Divider: `#e5e5e5` hoặc `#f0f0f0` (Rất nhẹ, tạo khối nhưng không gây rối).
  - Surface/Hover: `#f9f9f9` (Xám rất nhẹ cho các vùng hover hoặc nền table row).

## 2. Typography
- **Font chữ:** `Be Vietnam Pro` (Ưu tiên từ Google Fonts).
- **Trọng số (Weights):** 
  - Regular (400): Nội dung văn bản.
  - Medium (500): Nhãn, nút bấm.
  - SemiBold (600): Tiêu đề nhỏ, header của bảng.
  - Bold (700): Tiêu đề trang, tiêu đề quan trọng.
- **Kích thước:** Base font 14px cho admin, tiêu đề từ 18px - 24px.

## 3. Phong cách Component (Linear Inspired)
- **Thẻ (Tags/Badges):**
  - Padding nhỏ (2px 8px), bo góc nhẹ (4px).
  - Border mỏng 1px, màu nền nhạt hơn text.
  - Text viết hoa nhẹ (optional) hoặc chữ thường với font-weight 500.
- **Nút bấm (Buttons):**
  - Chiều cao chuẩn (32px - 36px cho admin).
  - Bo góc 4px - 6px (không bo tròn hoàn toàn).
  - Hiệu ứng hover: Làm đậm màu hoặc thêm shadow nhẹ.
- **Bảng (Tables):**
  - Tiêu đề cột có font-size nhỏ hơn, màu xám nhạt, font-weight 600.
  - Không kẻ khung dọc, chỉ kẻ ngang rất mỏng giữa các hàng.
  - Hover hàng: Đổi màu nền sang `#f9f9f9`.
- **Input/Forms:**
  - Border `#e5e5e5`, focus đổi sang màu `#9a2e24` với shadow nhẹ.

## 4. Nguyên tắc chung
- **Sạch sẽ (Clean):** Loại bỏ các thành phần trang trí thừa. Mỗi pixel đều phải có ý nghĩa.
- **Độ tương phản (Contrast):** Đảm bảo text trên nền trắng rõ ràng, dễ đọc cho việc quản trị dữ liệu lâu dài.
- **Khoảng trắng (Whitespace):** Sử dụng khoảng trắng rộng rãi để phân tách các khu vực chức năng, tránh cảm giác chật chội.

## 5. Ant Design trong DeepCulture Admin
- Ant Design chỉ dùng cho toast/feedback ngắn qua `message`.
- Không bọc root bằng `ConfigProvider`/`App` chỉ để dùng message.
- Không dùng các component Antd như `Table`, `Modal`, `Form`, `Input`, `Select`, `Pagination` trong module CRUD hiện tại nếu chưa có yêu cầu rõ.
- Toast/feedback ngắn dùng `import { message } from 'antd'` rồi gọi `message.success(...)`, `message.error(...)`, `message.warning(...)`, `message.loading(...)`.
- Không dùng `window.alert` cho thông báo nghiệp vụ thông thường.
- Với lỗi cần giữ trên màn hình để người dùng đọc hoặc sửa form, hiển thị alert inline trong layout thay vì chỉ toast.
- UI bảng, form, modal vẫn ưu tiên component tự viết + CSS Modules để giữ đúng thiết kế DeepCulture.
- Icon hành động vẫn ưu tiên `@phosphor-icons/react` để đồng bộ style sidebar/table action.
