import React from 'react';
import { Package, ListDashes, SignOut, Warehouse as WarehouseIcon, Stack } from '@phosphor-icons/react';
import styles from './Sidebar.module.css';

export default function Sidebar({ activeTab, setActiveTab, currentUser, onLogout }) {
  const menuItems = [
    { id: 'order', label: 'Quản Lý Đơn Hàng', icon: Package },
    { id: 'category', label: 'Danh Mục Sản Phẩm', icon: ListDashes },
    { id: 'product', label: 'Sản Phẩm', icon: Package },
    { id: 'warehouse', label: 'Kho Hàng', icon: WarehouseIcon },
    { id: 'inventory', label: 'Tồn Kho', icon: Stack },
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <h2 className={styles.title}>Quản Lý Kho</h2>
        <p className={styles.subtitle}>
          Xin chào, <strong style={{ color: 'var(--primary-color)' }}>{currentUser?.full_name}</strong>
        </p>
      </div>

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
