-- ==========================================
-- SQL SEED SCRIPT FOR MAIN DATABASE (Port 3307)
-- ==========================================

USE db;

-- Tắt kiểm tra khoá ngoại để dọn dẹp và chèn dữ liệu
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Dọn dẹp dữ liệu cũ trên Main DB
TRUNCATE TABLE order_package_shards;
TRUNCATE TABLE logs;
TRUNCATE TABLE product_stats;
TRUNCATE TABLE warehouse_stats;
TRUNCATE TABLE orders;
TRUNCATE TABLE products;
TRUNCATE TABLE categories;
TRUNCATE TABLE users;

-- 2. Thêm dữ liệu mẫu bảng users (Khách hàng)
INSERT INTO users (id, username, full_name) VALUES
(1, 'hoangnv', 'Nguyễn Văn Hoàng'),
(2, 'maitt', 'Trần Thị Mai'),
(3, 'namlh', 'Lê Hoàng Nam'),
(4, 'duchm', 'Phạm Minh Đức'),
(5, 'tuanha', 'Hoàng Anh Tuấn'),
(6, 'hongvt', 'Vũ Thị Hồng'),
(7, 'tribm', 'Bùi Minh Trí'),
(8, 'handn', 'Đặng Ngọc Hân');

-- 3. Thêm dữ liệu mẫu bảng categories (Danh mục)
INSERT INTO categories (id, name) VALUES
(1, 'Thời trang nam'),
(2, 'Thời trang nữ'),
(3, 'Đồ gia dụng'),
(4, 'Thiết bị điện tử'),
(5, 'Giày dép & Túi xách');

-- 4. Thêm dữ liệu mẫu bảng products (Sản phẩm)
INSERT INTO products (id, name, category_id, price, deleted_at) VALUES
-- Thời trang nam (Category 1)
(1, 'Áo polo nam', 1, 250000.00, NULL),
(2, 'Quần tây nam', 1, 380000.00, NULL),
(3, 'Quần jean nam', 1, 450000.00, NULL),
(4, 'Áo khoác gió nam', 1, 390000.00, NULL),
-- Thời trang nữ (Category 2)
(5, 'Đầm hoa nhí', 2, 490000.00, NULL),
(6, 'Chân váy midi', 2, 290000.00, NULL),
(7, 'Áo sơ mi lụa', 2, 320000.00, NULL),
(8, 'Quần culottes nữ', 2, 310000.00, NULL),
-- Đồ gia dụng (Category 3)
(9, 'Nồi chiên không dầu', 3, 1850000.00, NULL),
(10, 'Máy xay sinh tố', 3, 990000.00, NULL),
(11, 'Ấm siêu tốc Tefal', 3, 680000.00, NULL),
(12, 'Quạt đứng Senko', 3, 550000.00, NULL),
-- Thiết bị điện tử (Category 4)
(13, 'Tai nghe không dây Sony', 4, 1450000.00, NULL),
(14, 'Bàn phím cơ Dareu', 4, 620000.00, NULL),
(15, 'Chuột không dây Logitech', 4, 490000.00, NULL),
(16, 'Sạc dự phòng Anker', 4, 580000.00, NULL),
-- Giày dép & Túi xách (Category 5)
(17, 'Sneaker nam Biti\'s', 5, 890000.00, NULL),
(18, 'Giày cao gót Đông Hải', 5, 650000.00, NULL),
(19, 'Balo chống gù Miti', 5, 350000.00, NULL),
(20, 'Ví da nam Sen', 5, 290000.00, NULL);

-- 5. Thêm dữ liệu mẫu bảng orders (Đơn hàng giao rải từ tháng 5 đến đầu tháng 6)
INSERT INTO orders (id, user_id, shipping_address, total_amount, ordered_at) VALUES
(1, 1, '12 Láng Hạ, Ba Đình, Hà Nội', 870000.00, '2026-05-02 10:00:00'),
(2, 2, '180 Lê Lợi, Hải Châu, Đà Nẵng', 2830000.00, '2026-05-05 15:30:00'),
(3, 3, '350 Nguyễn Thị Minh Khai, Quận 3, TP.HCM', 890000.00, '2026-05-08 11:20:00'),
(4, 4, '45 Nguyễn Trãi, Thanh Xuân, Hà Nội', 1160000.00, '2026-05-11 09:15:00'),
(5, 5, '15 Mậu Thân, Ninh Kiều, Cần Thơ', 1570000.00, '2026-05-14 14:00:00'),
(6, 6, '52 Trần Hưng Đạo, Ninh Kiều, Cần Thơ', 1630000.00, '2026-05-16 16:45:00'),
(7, 7, '250 Điện Biên Phủ, Thanh Khê, Đà Nẵng', 1540000.00, '2026-05-19 13:10:00'),
(8, 8, '105 Lê Hồng Phong, Vũng Tàu', 1740000.00, '2026-05-22 10:20:00'),
(9, 1, '12 Láng Hạ, Ba Đình, Hà Nội', 1030000.00, '2026-05-25 15:30:00'),
(10, 3, '350 Nguyễn Thị Minh Khai, Quận 3, TP.HCM', 660000.00, '2026-05-27 08:45:00'),
(11, 2, '180 Lê Lợi, Hải Châu, Đà Nẵng', 1000000.00, '2026-05-29 11:15:00'),
(12, 5, '72 Hùng Vương, Nha Trang, Khánh Hòa', 1070000.00, '2026-05-31 14:30:00'),
(13, 6, '88 Song Hành, Thủ Đức, TP.HCM', 620000.00, '2026-06-01 09:00:00'),
(14, 7, '45 Nguyễn Trãi, Thanh Xuân, Hà Nội', 630000.00, '2026-06-01 16:00:00'),
(15, 8, '12 Láng Hạ, Ba Đình, Hà Nội', 1840000.00, '2026-06-02 10:00:00');

-- 6. Thêm dữ liệu mẫu bảng order_package_shards (Metadata ánh xạ sharding kiện hàng)
INSERT INTO order_package_shards (package_id, order_id, node_name) VALUES
-- Đơn hàng 1
(1, 1, 'north'),
(3, 1, 'south'),
-- Đơn hàng 2
(2, 2, 'central'),
-- Đơn hàng 3
(6, 3, 'south'),
-- Đơn hàng 4
(4, 4, 'north'),
(7, 4, 'north'),
-- Đơn hàng 5
(9, 5, 'south'),
(12, 5, 'south'),
-- Đơn hàng 6
(15, 6, 'south'),
(18, 6, 'south'),
-- Đơn hàng 7
(5, 7, 'central'),
-- Đơn hàng 8
(21, 8, 'south'),
(24, 8, 'south'),
-- Đơn hàng 9
(10, 9, 'north'),
(13, 9, 'north'),
-- Đơn hàng 10
(27, 10, 'south'),
-- Đơn hàng 11
(8, 11, 'central'),
-- Đơn hàng 12
(11, 12, 'central'),
-- Đơn hàng 13 (Đang giao hàng tháng 6)
(30, 13, 'south'),
-- Đơn hàng 14 (Đang giao hàng tháng 6)
(16, 14, 'north'),
-- Đơn hàng 15 (Chưa giao hàng)
(19, 15, 'north'),
(33, 15, 'south');

-- LƯU Ý QUAN TRỌNG:
-- Bảng `product_stats` và `warehouse_stats` được để trống.
-- Khi bạn bật giao diện Frontend và bấm nút "Cập nhật" (Sync) tại màn hình Thống kê,
-- hệ thống sẽ tự động quét và tính toán doanh thu từ 3 Node phụ để điền vào đây.

-- Bật lại kiểm tra khoá ngoại
SET FOREIGN_KEY_CHECKS = 1;
