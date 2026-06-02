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

-- 4. Thêm các nhà kho thuộc Miền Bắc (Region: North)
INSERT INTO warehouses (id, name, region, address) VALUES
(1, 'Kho Hà Nội Đông Anh', 'North', 'Số 5, KCN Đông Anh, Hà Nội'),
(2, 'Kho Hải Phòng Cát Hải', 'North', 'Cảng Đình Vũ, Quận Hải An, Hải Phòng');

-- 5. Khởi tạo tồn kho (inventories) của 2 kho Miền Bắc
-- Đã trừ đi hàng bán trong tháng 5 và tháng 6
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 1: Hà Nội Đông Anh
(1, 1, 1, 85, NOW()),  -- Đã xuất 1 (Đơn 1), 1 (Đơn 14)
(2, 2, 1, 48, NOW()),  -- Đã xuất 1 (Đơn 4), 1 (Đơn 14)
(3, 3, 1, 74, NOW()),  -- Đã xuất 1 (Đơn 9)
(4, 4, 1, 59, NOW()),  -- Đã xuất 1 (Đơn 15)
(5, 5, 1, 40, NOW()),
(6, 6, 1, 65, NOW()),
(7, 7, 1, 80, NOW()),
(8, 8, 1, 95, NOW()),
(9, 9, 1, 30, NOW()),
(10, 10, 1, 55, NOW()),
(11, 11, 1, 70, NOW()),
(12, 12, 1, 45, NOW()),
(13, 13, 1, 88, NOW()),
(14, 14, 1, 62, NOW()),
(15, 15, 1, 105, NOW()),
(16, 16, 1, 110, NOW()),
(17, 17, 1, 78, NOW()),
(18, 18, 1, 90, NOW()),
(19, 19, 1, 85, NOW()),
(20, 20, 1, 70, NOW()),
-- Kho 2: Hải Phòng Cát Hải
(21, 1, 2, 90, NOW()),
(22, 2, 2, 55, NOW()),
(23, 3, 2, 80, NOW()),
(24, 4, 2, 43, NOW()), -- Đã xuất 2 (Đơn 4)
(25, 5, 2, 45, NOW()),
(26, 6, 2, 70, NOW()),
(27, 7, 2, 85, NOW()),
(28, 8, 2, 90, NOW()),
(29, 9, 2, 35, NOW()),
(30, 10, 2, 50, NOW()),
(31, 11, 2, 75, NOW()),
(32, 12, 2, 40, NOW()),
(33, 13, 2, 95, NOW()),
(34, 14, 2, 60, NOW()),
(35, 15, 2, 100, NOW()),
(36, 16, 2, 119, NOW()), -- Đã xuất 1 (Đơn 9)
(37, 17, 2, 82, NOW()),
(38, 18, 2, 95, NOW()),
(39, 19, 2, 80, NOW()),
(40, 20, 2, 75, NOW());

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
(2, 4, 2, 1),
-- Kiện 7: 2 Áo khoác gió
(3, 7, 4, 2),
-- Kiện 10: 1 Quần jean nam
(4, 10, 3, 1),
-- Kiện 13: 1 Sạc dự phòng
(5, 13, 16, 1),
-- Kiện 16: 1 Áo polo, 1 Quần tây nam
(6, 16, 1, 1),
(7, 16, 2, 1),
-- Kiện 19: 1 Áo khoác gió
(8, 19, 4, 1);

SET FOREIGN_KEY_CHECKS = 1;
