-- ==========================================
-- SQL SEED SCRIPT FOR NODE 3: SOUTH (Port 3310)
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

-- 4. Thêm các nhà kho thuộc Miền Nam (Region: South)
INSERT INTO warehouses (id, name, region, address) VALUES
(4, 'Kho TP.HCM', 'South', 'Khu chế xuất Linh Trung, Thủ Đức, TP.HCM'),
(5, 'Kho Cần Thơ', 'South', 'KCN Hưng Phú, Cái Răng, Cần Thơ');

-- 5. Khởi tạo tồn kho (inventories) của 2 kho Miền Nam
-- Đã trừ số lượng hàng của các đơn hàng đã đặt
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 4: TP.HCM Thủ Đức
(3, 1, 4, 110, NOW()),
(6, 2, 4, 80, NOW()),
(9, 3, 4, 95, NOW()),
(12, 4, 4, 85, NOW()),
(15, 5, 4, 60, NOW()),
(18, 6, 4, 75, NOW()),
(21, 7, 4, 90, NOW()),
(24, 8, 4, 99, NOW()),  -- Đã xuất 1 (Đơn 10)
(27, 9, 4, 45, NOW()),
(30, 10, 4, 60, NOW()),
(33, 11, 4, 80, NOW()),
(36, 12, 4, 55, NOW()),
(39, 13, 4, 113, NOW()), -- Đã xuất 1 (Đơn 8), 1 (Đơn 15)
(42, 14, 4, 73, NOW()),  -- Đã xuất 1 (Đơn 1), 1 (Đơn 13)
(45, 15, 4, 119, NOW()),
(48, 16, 4, 130, NOW()),
(51, 17, 4, 88, NOW()),  -- Đã xuất 1 (Đơn 3), 1 (Đơn 5)
(54, 18, 4, 104, NOW()), -- Đã xuất 1 (Đơn 6)
(57, 19, 4, 89, NOW()),  -- Đã xuất 1 (Đơn 10)
(60, 20, 4, 85, NOW()),
-- Kho 5: Cần Thơ Cái Răng
(63, 1, 5, 95, NOW()),
(66, 2, 5, 65, NOW()),
(69, 3, 5, 85, NOW()),
(72, 4, 5, 70, NOW()),
(75, 5, 5, 48, NOW()),  -- Đã xuất 2 (Đơn 6)
(78, 6, 5, 65, NOW()),
(81, 7, 5, 75, NOW()),
(84, 8, 5, 80, NOW()),
(87, 9, 5, 35, NOW()),
(90, 10, 5, 50, NOW()),
(93, 11, 5, 69, NOW()), -- Đã xuất 1 (Đơn 5)
(96, 12, 5, 45, NOW()),
(99, 13, 5, 90, NOW()),
(102, 14, 5, 55, NOW()),
(105, 15, 5, 100, NOW()),
(108, 16, 5, 110, NOW()),
(111, 17, 5, 79, NOW()), 
(114, 18, 5, 90, NOW()),
(117, 19, 5, 75, NOW()),
(120, 20, 5, 67, NOW()); -- Đã xuất 1 (Đơn 8)

-- 6. Kiện hàng (packages) gán ID thủ công tuân thủ auto-increment offset=3, increment=3
INSERT INTO packages (id, order_id, warehouse_id, status, created_at, delivered_at) VALUES
(3, 1, 4, 'Delivered', '2026-05-02 10:00:00', '2026-05-04 14:00:00'),
(6, 3, 4, 'Delivered', '2026-05-08 11:20:00', '2026-05-09 16:00:00'),
(9, 5, 5, 'Delivered', '2026-05-14 14:00:00', '2026-05-16 11:20:00'),
(12, 5, 4, 'Delivered', '2026-05-14 14:00:00', '2026-05-16 11:20:00'),
(15, 6, 5, 'Delivered', '2026-05-16 16:45:00', '2026-05-18 17:00:00'),
(18, 6, 4, 'Delivered', '2026-05-16 16:45:00', '2026-05-18 17:00:00'),
(21, 8, 4, 'Delivered', '2026-05-22 10:20:00', '2026-05-24 14:15:00'),
(24, 8, 5, 'Delivered', '2026-05-22 10:20:00', '2026-05-24 14:15:00'),
(27, 10, 4, 'Delivered', '2026-05-27 08:45:00', '2026-05-28 16:00:00'),
(30, 13, 4, 'Shipping', '2026-06-01 09:00:00', NULL),
(33, 15, 4, 'Pending', '2026-06-02 10:00:00', NULL);

-- 7. Chi tiết kiện hàng (package_details)
INSERT INTO package_details (id, package_id, product_id, quantity) VALUES
-- Kiện 3 (Đơn 1): 1 Bàn phím cơ
(3, 3, 14, 1),
-- Kiện 6 (Đơn 3): 1 Sneaker nam
(6, 6, 17, 1),
-- Kiện 9 (Đơn 5): 1 Ấm siêu tốc
(9, 9, 11, 1),
-- Kiện 12 (Đơn 5): 1 Sneaker nam
(12, 12, 17, 1),
-- Kiện 15 (Đơn 6): 2 Đầm hoa nhí
(15, 15, 5, 2),
-- Kiện 18 (Đơn 6): 1 Giày cao gót
(18, 18, 18, 1),
-- Kiện 21 (Đơn 8): 1 Tai nghe không dây
(21, 21, 13, 1),
-- Kiện 24 (Đơn 8): 1 Ví da nam
(24, 24, 20, 1),
-- Kiện 27 (Đơn 10): 1 Balo học sinh, 1 Quần culottes
(27, 27, 19, 1),
(30, 27, 8, 1),
-- Kiện 30 (Đơn 13): 1 Bàn phím cơ
(33, 30, 14, 1),
-- Kiện 33 (Đơn 15): 1 Tai nghe không dây
(36, 33, 13, 1);

SET FOREIGN_KEY_CHECKS = 1;
