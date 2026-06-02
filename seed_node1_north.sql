-- ==========================================
-- SQL SEED SCRIPT FOR NODE 1: NORTH (Port 3308)
-- ==========================================

USE db;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Dọn dẹp dữ liệu cũ
TRUNCATE TABLE package_details;
TRUNCATE TABLE packages;
TRUNCATE TABLE inventories;
TRUNCATE TABLE warehouses;
TRUNCATE TABLE products;
TRUNCATE TABLE categories;

-- 2. Thêm dữ liệu mẫu danh mục (Read-replicated sao chép từ Main)
INSERT INTO categories (id, name) VALUES
(1, 'Thời trang nam'),
(2, 'Thời trang nữ'),
(3, 'Đồ gia dụng'),
(4, 'Thiết bị điện tử'),
(5, 'Giày dép & Túi xách');

-- 3. Thêm dữ liệu mẫu sản phẩm (Read-replicated sao chép từ Main)
INSERT INTO products (id, name, category_id, price, deleted_at) VALUES
(1, 'Áo polo nam', 1, 250000.00, NULL),
(2, 'Quần tây nam', 1, 380000.00, NULL),
(3, 'Quần jean nam', 1, 450000.00, NULL),
(4, 'Áo khoác gió nam', 1, 390000.00, NULL),
(5, 'Đầm hoa nhí', 2, 490000.00, NULL),
(6, 'Chân váy midi', 2, 290000.00, NULL),
(7, 'Áo sơ mi lụa', 2, 320000.00, NULL),
(8, 'Quần culottes nữ', 2, 310000.00, NULL),
(9, 'Nồi chiên không dầu', 3, 1850000.00, NULL),
(10, 'Máy xay sinh tố', 3, 990000.00, NULL),
(11, 'Ấm siêu tốc Tefal', 3, 680000.00, NULL),
(12, 'Quạt đứng Senko', 3, 550000.00, NULL),
(13, 'Tai nghe không dây Sony', 4, 1450000.00, NULL),
(14, 'Bàn phím cơ Dareu', 4, 620000.00, NULL),
(15, 'Chuột không dây Logitech', 4, 490000.00, NULL),
(16, 'Sạc dự phòng Anker', 4, 580000.00, NULL),
(17, 'Sneaker nam Biti\'s', 5, 890000.00, NULL),
(18, 'Giày cao gót Đông Hải', 5, 650000.00, NULL),
(19, 'Balo chống gù Miti', 5, 350000.00, NULL),
(20, 'Ví da nam Sen', 5, 290000.00, NULL);

-- 4. Thêm các nhà kho thuộc Miền Bắc (Region: North)
INSERT INTO warehouses (id, name, region, address) VALUES
(1, 'Kho Hà Nội', 'North', 'Số 5, KCN Đông Anh, Hà Nội'),
(2, 'Kho Hải Phòng', 'North', 'Cảng Đình Vũ, Quận Hải An, Hải Phòng');

-- 5. Khởi tạo tồn kho (inventories) của 2 kho Miền Bắc
-- Đã trừ đi hàng bán trong tháng 5 và tháng 6
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 1: Hà Nội Đông Anh
(1, 1, 1, 85, NOW()),  -- Đã xuất 1 (Đơn 1), 1 (Đơn 14)
(4, 2, 1, 48, NOW()),  -- Đã xuất 1 (Đơn 4), 1 (Đơn 14)
(7, 3, 1, 74, NOW()),  -- Đã xuất 1 (Đơn 9)
(10, 4, 1, 59, NOW()),  -- Đã xuất 1 (Đơn 15)
(13, 5, 1, 40, NOW()),
(16, 6, 1, 65, NOW()),
(19, 7, 1, 80, NOW()),
(22, 8, 1, 95, NOW()),
(25, 9, 1, 30, NOW()),
(28, 10, 1, 55, NOW()),
(31, 11, 1, 70, NOW()),
(34, 12, 1, 45, NOW()),
(37, 13, 1, 88, NOW()),
(40, 14, 1, 62, NOW()),
(43, 15, 1, 105, NOW()),
(46, 16, 1, 110, NOW()),
(49, 17, 1, 78, NOW()),
(52, 18, 1, 90, NOW()),
(55, 19, 1, 85, NOW()),
(58, 20, 1, 70, NOW()),
-- Kho 2: Hải Phòng Cát Hải
(61, 1, 2, 90, NOW()),
(64, 2, 2, 55, NOW()),
(67, 3, 2, 80, NOW()),
(70, 4, 2, 43, NOW()), -- Đã xuất 2 (Đơn 4)
(73, 5, 2, 45, NOW()),
(76, 6, 2, 70, NOW()),
(79, 7, 2, 85, NOW()),
(82, 8, 2, 90, NOW()),
(85, 9, 2, 35, NOW()),
(88, 10, 2, 50, NOW()),
(91, 11, 2, 75, NOW()),
(94, 12, 2, 40, NOW()),
(97, 13, 2, 95, NOW()),
(100, 14, 2, 60, NOW()),
(103, 15, 2, 100, NOW()),
(106, 16, 2, 119, NOW()), -- Đã xuất 1 (Đơn 9)
(109, 17, 2, 82, NOW()),
(112, 18, 2, 95, NOW()),
(115, 19, 2, 80, NOW()),
(118, 20, 2, 75, NOW());

-- 6. Kiện hàng (packages) gán ID thủ công tuân thủ auto-increment offset=1, increment=3
INSERT INTO packages (id, order_id, warehouse_id, status, created_at, delivered_at) VALUES
(1, 1, 1, 'Delivered', '2026-05-02 10:00:00', '2026-05-04 14:00:00'),
(4, 4, 1, 'Delivered', '2026-05-11 09:15:00', '2026-05-13 15:30:00'),
(7, 4, 2, 'Delivered', '2026-05-11 09:15:00', '2026-05-13 15:30:00'),
(10, 9, 1, 'Delivered', '2026-05-25 15:30:00', '2026-05-27 11:00:00'),
(13, 9, 2, 'Delivered', '2026-05-25 15:30:00', '2026-05-27 11:00:00'),
(16, 14, 1, 'Shipping', '2026-06-01 16:00:00', NULL),
(19, 15, 1, 'Pending', '2026-06-02 10:00:00', NULL);

-- 7. Chi tiết kiện hàng (package_details)
INSERT INTO package_details (id, package_id, product_id, quantity) VALUES
-- Kiện 1: 1 Áo polo
(1, 1, 1, 1),
-- Kiện 4: 1 Quần tây nam
(4, 4, 2, 1),
-- Kiện 7: 2 Áo khoác gió
(7, 7, 4, 2),
-- Kiện 10: 1 Quần jean nam
(10, 10, 3, 1),
-- Kiện 13: 1 Sạc dự phòng
(13, 13, 16, 1),
-- Kiện 16: 1 Áo polo, 1 Quần tây nam
(16, 16, 1, 1),
(19, 16, 2, 1),
-- Kiện 19: 1 Áo khoác gió
(22, 19, 4, 1);

SET FOREIGN_KEY_CHECKS = 1;
