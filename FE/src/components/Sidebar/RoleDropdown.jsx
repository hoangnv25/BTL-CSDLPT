import React, { useState, useEffect } from 'react';
import styles from './Sidebar.module.css';

export default function RoleDropdown({ currentOption, onChange }) {
  const [warehouses, setWarehouses] = useState([]);
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchWarehouses = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/warehouse`);
        if (response.ok) {
          const data = await response.json();
          setWarehouses(data);
        }
      } catch (err) {
        console.error("Lỗi fetch warehouses cho dropdown:", err);
      }
    };
    fetchWarehouses();
  }, []);

  return (
    <div className={styles.roleDropdownContainer}>
      <label className={styles.roleDropdownLabel}>Vai trò & Khu vực:</label>
      <select 
        className={styles.roleSelect} 
        value={currentOption} 
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="admin">Quản trị</option>
        <option value="host">Quản lý tổng</option>
        <option value="user">Khách Hàng</option>
        {warehouses.map(w => (
          <option key={w.id} value={`manager_${w.id}`}>
            {w.name} 
          </option>
        ))}
      </select>
    </div>
  );
}
