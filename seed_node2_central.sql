-- ==========================================
-- SQL SEED SCRIPT FOR NODE 2: CENTRAL (Port 3309)
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

-- 4. Thêm các nhà kho thuộc Miền Trung (Region: Central)
INSERT INTO warehouses (id, name, region, address) VALUES
(3, 'Kho Đà Nẵng', 'Central', 'Đường số 2, KCN Hòa Khánh, Liên Chiểu, Đà Nẵng');

-- 5. Khởi tạo tồn kho (inventories) của Kho Miền Trung
-- Đã trừ số lượng hàng của các đơn hàng đã đặt
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 3: Đà Nẵng Liên Chiểu
(2, 1, 3, 70, NOW()),
(5, 2, 3, 55, NOW()),
(8, 3, 3, 65, NOW()),
(11, 4, 3, 40, NOW()),
(14, 5, 3, 38, NOW()),
(17, 6, 3, 48, NOW()),  -- Đã xuất 2 (Đơn 12)
(20, 7, 3, 49, NOW()),  -- Đã xuất 1 (Đơn 11)
(23, 8, 3, 72, NOW()),
(26, 9, 3, 24, NOW()),  -- Đã xuất 1 (Đơn 2)
(29, 10, 3, 29, NOW()), -- Đã xuất 1 (Đơn 7)
(32, 11, 3, 49, NOW()), -- Đã xuất 1 (Đơn 11)
(35, 12, 3, 34, NOW()), -- Đã xuất 1 (Đơn 7)
(38, 13, 3, 60, NOW()),
(41, 14, 3, 45, NOW()),
(44, 15, 3, 77, NOW()), -- Đã xuất 2 (Đơn 2), 1 (Đơn 12)
(47, 16, 3, 85, NOW()),
(50, 17, 3, 50, NOW()),
(53, 18, 3, 55, NOW()),
(56, 19, 3, 60, NOW()),
(59, 20, 3, 48, NOW());

-- 6. Kiện hàng (packages) gán ID thủ công tuân thủ auto-increment offset=2, increment=3
INSERT INTO packages (id, order_id, warehouse_id, status, created_at, delivered_at) VALUES
(2, 2, 3, 'Delivered', '2026-05-05 15:30:00', '2026-05-07 10:30:00'),
(5, 7, 3, 'Delivered', '2026-05-19 13:10:00', '2026-05-21 09:30:00'),
(8, 11, 3, 'Delivered', '2026-05-29 11:15:00', '2026-05-30 14:00:00'),
(11, 12, 3, 'Delivered', '2026-05-31 14:30:00', '2026-06-01 16:30:00');

-- 7. Chi tiết kiện hàng (package_details)
INSERT INTO package_details (id, package_id, product_id, quantity) VALUES
-- Kiện 2 (Đơn 2): 1 Nồi chiên, 2 Chuột
(2, 2, 9, 1),
(5, 2, 15, 2),
-- Kiện 5 (Đơn 7): 1 Máy xay, 1 Quạt đứng
(8, 5, 10, 1),
(11, 5, 12, 1),
-- Kiện 8 (Đơn 11): 1 Áo sơ mi, 1 Ấm siêu tốc
(14, 8, 7, 1),
(17, 8, 11, 1),
-- Kiện 11 (Đơn 12): 2 Chân váy, 1 Chuột
(20, 11, 6, 2),
(23, 11, 15, 1);

SET FOREIGN_KEY_CHECKS = 1;
