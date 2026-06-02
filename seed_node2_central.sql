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

-- 4. Thêm các nhà kho thuộc Miền Trung (Region: Central)
INSERT INTO warehouses (id, name, region, address) VALUES
(3, 'Kho Đà Nẵng', 'Central', 'Đường số 2, KCN Hòa Khánh, Liên Chiểu, Đà Nẵng');

-- 5. Khởi tạo tồn kho (inventories) của Kho Miền Trung
-- Đã trừ số lượng hàng của các đơn hàng đã đặt
INSERT INTO inventories (id, product_id, warehouse_id, stock_quantity, updated_at) VALUES
-- Kho 3: Đà Nẵng Liên Chiểu
(1, 1, 3, 70, NOW()),
(2, 2, 3, 55, NOW()),
(3, 3, 3, 65, NOW()),
(4, 4, 3, 40, NOW()),
(5, 5, 3, 38, NOW()),
(6, 6, 3, 48, NOW()),  -- Đã xuất 2 (Đơn 12)
(7, 7, 3, 49, NOW()),  -- Đã xuất 1 (Đơn 11)
(8, 8, 3, 72, NOW()),
(9, 9, 3, 24, NOW()),  -- Đã xuất 1 (Đơn 2)
(10, 10, 3, 29, NOW()), -- Đã xuất 1 (Đơn 7)
(11, 11, 3, 49, NOW()), -- Đã xuất 1 (Đơn 11)
(12, 12, 3, 34, NOW()), -- Đã xuất 1 (Đơn 7)
(13, 13, 3, 60, NOW()),
(14, 14, 3, 45, NOW()),
(15, 15, 3, 77, NOW()), -- Đã xuất 2 (Đơn 2), 1 (Đơn 12)
(16, 16, 3, 85, NOW()),
(17, 17, 3, 50, NOW()),
(18, 18, 3, 55, NOW()),
(19, 19, 3, 60, NOW()),
(20, 20, 3, 48, NOW());

-- 6. Kiện hàng (packages) gán ID thủ công tuân thủ auto-increment offset=2, increment=3
INSERT INTO packages (id, order_id, warehouse_id, status, created_at, delivered_at) VALUES
(2, 2, 3, 'Delivered', '2026-05-05 15:30:00', '2026-05-07 10:30:00'),
(5, 7, 3, 'Delivered', '2026-05-19 13:10:00', '2026-05-21 09:30:00'),
(8, 11, 3, 'Delivered', '2026-05-29 11:15:00', '2026-05-30 14:00:00'),
(11, 12, 3, 'Delivered', '2026-05-31 14:30:00', '2026-06-01 16:30:00');

-- 7. Chi tiết kiện hàng (package_details)
INSERT INTO package_details (id, package_id, product_id, quantity) VALUES
-- Kiện 2 (Đơn 2): 1 Nồi chiên, 2 Chuột
(1, 2, 9, 1),
(2, 2, 15, 2),
-- Kiện 5 (Đơn 7): 1 Máy xay, 1 Quạt đứng
(3, 5, 10, 1),
(4, 5, 12, 1),
-- Kiện 8 (Đơn 11): 1 Áo sơ mi, 1 Ấm siêu tốc
(5, 8, 7, 1),
(6, 8, 11, 1),
-- Kiện 11 (Đơn 12): 2 Chân váy, 1 Chuột
(7, 11, 6, 2),
(8, 11, 15, 1);

SET FOREIGN_KEY_CHECKS = 1;
