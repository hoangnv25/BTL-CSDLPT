import React from 'react';
import { Package, ListDashes, SignOut, Warehouse as WarehouseIcon, Stack, Truck, Receipt, Eye, Database, ChartBar } from '@phosphor-icons/react';
import styles from './Sidebar.module.css';
import RoleDropdown from './RoleDropdown';
import { roleAllowedPages } from './roles';

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  currentUser, 
  onLogout, 
  currentOption = 'admin', 
  onOptionChange 
}) {
  
  // Lấy role từ currentOption
  let role = 'admin';
  if (currentOption === 'user') {
    role = 'user';
  } else if (currentOption.startsWith('manager_')) {
    role = 'manager';
  }

  const allMenuItems = [
    { id: 'order', label: 'Quản Lý Đơn Hàng', icon: Package },
    { id: 'stats', label: 'Thống Kê', icon: ChartBar },
    { id: 'category', label: 'Danh Mục Sản Phẩm', icon: ListDashes },
    { id: 'product', label: 'Sản Phẩm', icon: Package },
    { id: 'warehouse', label: 'Kho Hàng', icon: WarehouseIcon },
    { id: 'inventory', label: 'Tồn Kho', icon: Stack },
    { id: 'package', label: 'Kiện Hàng', icon: Truck },
    { id: 'package_warehouse', label: 'Kiện Hàng Theo Kho', icon: Truck },
    { id: 'my_order', label: 'Đơn Hàng', icon: Receipt },
    { id: 'product_view', label: 'Xem Sản Phẩm', icon: Eye },
    { id: 'inventory_warehouse', label: 'Tồn Kho Theo Kho', icon: Database },
  ];

  // Lọc các tab menu được hiển thị dựa trên role hiện tại
  const allowed = roleAllowedPages[role] || [];
  const menuItems = allMenuItems.filter(item => allowed.includes(item.id));

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <h2 className={styles.title}>CSDL Phân tán</h2>
        <p className={styles.subtitle}>
          Xin chào, <strong style={{ color: 'var(--primary-color)' }}>{currentUser?.full_name}</strong>
        </p>
      </div>

      {/* Dropdown chuyển đổi vai trò và kho */}
      <RoleDropdown currentOption={currentOption} onChange={onOptionChange} />

      <nav className={styles.menu}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`${styles.menuItem} ${isActive ? styles.active : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={20} weight={isActive ? 'fill' : 'regular'} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className={styles.footer}>
        <button className={styles.logoutBtn} onClick={onLogout}>
          <SignOut size={20} />
          Đăng Xuất
        </button>
      </div>
    </aside>
  );
}
