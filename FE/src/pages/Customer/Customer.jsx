import React, { useState, useEffect } from 'react';
import { MagnifyingGlass, User } from '@phosphor-icons/react';
import { Pagination } from 'antd';
import styles from './Customer.module.css';

export default function Customer() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Search state
  const [searchTerm, setSearchTerm] = useState('');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/users`);
      if (!response.ok) throw new Error('Không thể tải danh sách khách hàng/người dùng');
      const data = await response.json();
      setUsers(data);
      setCurrentPage(1); // Reset page on fetch
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Filter logic
  const filteredUsers = users.filter(user => {
    const term = searchTerm.toLowerCase();
    return (
      user.username.toLowerCase().includes(term) ||
      user.full_name.toLowerCase().includes(term) ||
      user.id.toString().includes(term)
    );
  });

  // Pagination Logic
  const totalItems = filteredUsers.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE) || 1;
  const currentData = filteredUsers.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const renderPagination = () => {
    return (
      <div className={styles.paginationContainer}>
        <span className={styles.pageInfo}>
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, totalItems)} trong tổng số {totalItems} bản ghi
        </span>
        <Pagination
          current={currentPage}
          total={totalItems}
          pageSize={ITEMS_PER_PAGE}
          onChange={(page) => setCurrentPage(page)}
          showSizeChanger={false}
        />
      </div>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>Quản Lý Khách Hàng</h1>
      </div>

      {/* Toolbar với ô tìm kiếm */}
      <div className={styles.toolbar}>
        <div className={styles.searchGroup}>
          <MagnifyingGlass size={18} style={{ color: 'var(--text-secondary)' }} />
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Tìm kiếm"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '15%' }}>ID Người Dùng</th>
                <th className={styles.th} style={{ width: '35%' }}>Tên Đăng Nhập</th>
                <th className={styles.th} style={{ width: '50%' }}>Họ Và Tên</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="3" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="3" className={styles.emptyState}>Không tìm thấy khách hàng nào.</td>
                </tr>
              ) : (
                currentData.map((user) => (
                  <tr key={user.id} className={styles.tableRow}>
                    <td className={styles.td}>{user.id}</td>
                    <td className={styles.td}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <User size={16} style={{ color: 'var(--primary-color)' }} />
                        <strong>{user.username}</strong>
                      </div>
                    </td>
                    <td className={styles.td}>{user.full_name}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && totalItems > 0 && renderPagination()}
      </div>
    </div>
  );
}
