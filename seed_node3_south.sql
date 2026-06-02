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
(1, 'Áo thun polo nam cổ bẻ cotton tăm', 1, 250000.00, NULL),
(2, 'Quần dài tây nam ống đứng lịch lãm', 1, 380000.00, NULL),
(3, 'Quần jean nam co giãn màu xanh chàm', 1, 450000.00, NULL),
(4, 'Áo khoác gió nam hai lớp chống nước', 1, 390000.00, NULL),
(5, 'Đầm hoa nhí voan tơ dáng xòe dài', 2, 490000.00, NULL),
(6, 'Chân váy midi chữ A dáng dài công sở', 2, 290000.00, NULL),
(7, 'Áo sơ mi lụa tơ tằm cổ V thanh lịch', 2, 320000.00, NULL),
(8, 'Quần culottes vải tuyết mưa cạp cao', 2, 310000.00, NULL),
(9, 'Nồi chiên không dầu Philips HD9252 4.1L', 3, 1850000.00, NULL),
(10, 'Máy xay sinh tố cầm tay Braun MultiQuick', 3, 990000.00, NULL),
(11, 'Ấm siêu tốc Tefal Safe\'tea 1.7L', 3, 680000.00, NULL),
(12, 'Quạt cây đứng lửng Senko LTS1636', 3, 550000.00, NULL),
(13, 'Tai nghe không dây Sony WF-C500 chống nước', 4, 1450000.00, NULL),
(14, 'Bàn phím cơ Dareu EK87 Multi-LED', 4, 620000.00, NULL),
(15, 'Chuột không dây Logitech Pebble M350', 4, 490000.00, NULL),
(16, 'Sạc dự phòng Anker PowerCore Slim 10000mAh', 4, 580000.00, NULL),
(17, 'Giày sneaker nam Biti\'s Hunter Street', 5, 890000.00, NULL),
(18, 'Giày cao gót nữ Đông Hải da mềm 5cm', 5, 650000.00, NULL),
(19, 'Balo học sinh chống gù Miti bảo vệ cột sống', 5, 350000.00, NULL),
(20, 'Ví da nam da bò thật nhỏ gọn Sen', 5, 290000.00, NULL);

-- 4. Thêm các nhà kho thuộc Miền Nam (Region: South)
INSERT INTO warehouses (id, name, region, address) VALUES
(4, 'Kho TP.HCM', 'South', 'Khu chế xuất Linh Trung, Thủ Đức, TP.HCM'),
(5, 'Kho Cần Thơ', 'South', 'KCN Hưng Phú, Cái Răng, Cần Thơ');

-- 5. Khởi tạo tồn kho (inventories) của 2 kho Miền Nam
-- Đã trừ số lượng hàng của các đơn hàng đã đặt
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 4: TP.HCM Thủ Đức
(1, 1, 4, 110, NOW()),
(2, 2, 4, 80, NOW()),
(3, 3, 4, 95, NOW()),
(4, 4, 4, 85, NOW()),
(5, 5, 4, 60, NOW()),
(6, 6, 4, 75, NOW()),
(7, 7, 4, 90, NOW()),
(8, 8, 4, 99, NOW()),  -- Đã xuất 1 (Đơn 10)
(9, 9, 4, 45, NOW()),
(10, 10, 4, 60, NOW()),
(11, 11, 4, 80, NOW()),
(12, 12, 4, 55, NOW()),
(13, 13, 4, 113, NOW()), -- Đã xuất 1 (Đơn 8), 1 (Đơn 15)
(14, 14, 4, 73, NOW()),  -- Đã xuất 1 (Đơn 1), 1 (Đơn 13)
(15, 15, 4, 119, NOW()),
(16, 16, 4, 130, NOW()),
(17, 17, 4, 88, NOW()),  -- Đã xuất 1 (Đơn 3), 1 (Đơn 5)
(18, 18, 4, 104, NOW()), -- Đã xuất 1 (Đơn 6)
(19, 19, 4, 89, NOW()),  -- Đã xuất 1 (Đơn 10)
(20, 20, 4, 85, NOW()),
-- Kho 5: Cần Thơ Cái Răng
(21, 1, 5, 95, NOW()),
(22, 2, 5, 65, NOW()),
(23, 3, 5, 85, NOW()),
(24, 4, 5, 70, NOW()),
(25, 5, 5, 48, NOW()),  -- Đã xuất 2 (Đơn 6)
(26, 6, 5, 65, NOW()),
(27, 7, 5, 75, NOW()),
(28, 8, 5, 80, NOW()),
(29, 9, 5, 35, NOW()),
(30, 10, 5, 50, NOW()),
(31, 11, 5, 69, NOW()), -- Đã xuất 1 (Đơn 5)
(32, 12, 5, 45, NOW()),
(33, 13, 5, 90, NOW()),
(34, 14, 5, 55, NOW()),
(35, 15, 5, 100, NOW()),
(36, 16, 5, 110, NOW()),
(37, 17, 5, 79, NOW()), 
(38, 18, 5, 90, NOW()),
(39, 19, 5, 75, NOW()),
(40, 20, 5, 67, NOW()); -- Đã xuất 1 (Đơn 8)

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
(1, 3, 14, 1),
-- Kiện 6 (Đơn 3): 1 Sneaker nam
(2, 6, 17, 1),
-- Kiện 9 (Đơn 5): 1 Ấm siêu tốc
(3, 9, 11, 1),
-- Kiện 12 (Đơn 5): 1 Sneaker nam
(4, 12, 17, 1),
-- Kiện 15 (Đơn 6): 2 Đầm hoa nhí
(5, 15, 5, 2),
-- Kiện 18 (Đơn 6): 1 Giày cao gót
(6, 18, 18, 1),
-- Kiện 21 (Đơn 8): 1 Tai nghe không dây
(7, 21, 13, 1),
-- Kiện 24 (Đơn 8): 1 Ví da nam
(8, 24, 20, 1),
-- Kiện 27 (Đơn 10): 1 Balo học sinh, 1 Quần culottes
(9, 27, 19, 1),
(10, 27, 8, 1),
-- Kiện 30 (Đơn 13): 1 Bàn phím cơ
(11, 30, 14, 1),
-- Kiện 33 (Đơn 15): 1 Tai nghe không dây
(12, 33, 13, 1);

SET FOREIGN_KEY_CHECKS = 1;
