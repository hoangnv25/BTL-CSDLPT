import React, { useState, useEffect } from 'react';
import { Truck, MapPin, CalendarBlank, ShoppingBag } from '@phosphor-icons/react';
import styles from './Package.module.css';

export default function Package() {
  const [packages, setPackages] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterWarehouse, setFilterWarehouse] = useState('');
  const [updatingPackageId, setUpdatingPackageId] = useState(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  const fetchWarehouses = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/warehouse`);
      if (res.ok) {
        const data = await res.json();
        setWarehouses(data);
      }
    } catch (err) {
      console.error("Lỗi lấy danh sách kho:", err);
    }
  };

  const fetchPackages = async () => {
    setLoading(true);
    setError('');
    try {
      let endpoint = `${API_BASE_URL}/package`;
      if (filterWarehouse) {
        endpoint += `?warehouse_id=${filterWarehouse}`;
      }
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Không thể tải danh sách kiện hàng');
      const data = await response.json();
      setPackages(data);
      setCurrentPage(1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  useEffect(() => {
    fetchPackages();
  }, [filterWarehouse]);

  const handleUpdateStatus = async (packageId, newStatus) => {
    setUpdatingPackageId(packageId);
    try {
      const response = await fetch(`${API_BASE_URL}/package/${packageId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) throw new Error('Cập nhật trạng thái thất bại');
      
      // Cập nhật state nội bộ
      setPackages(prev => 
        prev.map(pkg => pkg.id === packageId ? { ...pkg, status: newStatus } : pkg)
      );
    } catch (err) {
      alert(err.message);
    } finally {
      setUpdatingPackageId(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('vi-VN');
  };

  const formatCurrency = (amount) => {
    if (!amount) return '0';
    return Number(amount).toLocaleString('vi-VN') + ' đ';
  };

  // Pagination Logic
  const totalPages = Math.ceil(packages.length / ITEMS_PER_PAGE) || 1;
  const currentData = packages.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>Quản Lý Kiện Hàng</h1>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Kho hàng:</label>
          <select 
            className={styles.filterSelect}
            value={filterWarehouse}
            onChange={(e) => setFilterWarehouse(e.target.value)}
          >
            <option value="">-- Tất cả kho --</option>
            {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
        </div>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '10%' }}>ID Kiện</th>
                <th className={styles.th} style={{ width: '18%' }}>Kho Xuất</th>
                <th className={styles.th} style={{ width: '22%' }}>Khách Hàng / Đơn Hàng</th>
                <th className={styles.th} style={{ width: '30%' }}>Danh Sách Sản Phẩm</th>
                <th className={styles.th} style={{ width: '12%', textAlign: 'right' }}>Ngày Tạo</th>
                <th className={styles.th} style={{ width: '8%', textAlign: 'right' }}>Trạng Thái</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="6" className={styles.emptyState}>Không có kiện hàng nào.</td>
                </tr>
              ) : (
                currentData.map((pkg) => (
                  <tr key={pkg.id} className={styles.tableRow}>
                    <td className={styles.td}>#{pkg.id}</td>
                    <td className={styles.td}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <MapPin size={16} />
                        {pkg.warehouse?.name}
                      </div>
                    </td>
                    <td className={styles.td}>
                      <div>
                        <strong>{pkg.order?.user?.full_name || pkg.order?.user?.username}</strong>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                          Đơn hàng #{pkg.order?.id} - {formatCurrency(pkg.order?.total_amount)}
                        </div>
                      </div>
                    </td>
                    <td className={styles.td}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {pkg.items && pkg.items.map((item, idx) => (
                          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '13px' }}>
                            <ShoppingBag size={14} color="var(--text-secondary)" />
                            <span>{item.product?.name}</span>
                            <strong style={{ color: 'var(--primary-color)' }}>x{item.quantity}</strong>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontSize: '13px', color: 'var(--text-secondary)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', justifyContent: 'flex-end' }}>
                        <CalendarBlank size={14} />
                        {formatDate(pkg.created_at)}
                      </div>
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right' }}>
                      <select
                        value={pkg.status || 'Pending'}
                        onChange={(e) => handleUpdateStatus(pkg.id, e.target.value)}
                        disabled={updatingPackageId === pkg.id}
                        className={`${styles.packageBadgeSelect} ${styles[`status${pkg.status || 'Pending'}`]}`}
                      >
                        <option value="Pending">Pending</option>
                        <option value="Shipping">Shipping</option>
                        <option value="Delivered">Delivered</option>
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && packages.length > 0 && (
          <div className={styles.pagination}>
            <span className={styles.pageInfo}>
              Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, packages.length)} trong tổng số {packages.length} kiện hàng
            </span>
            <button className={styles.pageBtn} onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}>
              Trước
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`${styles.pageBtn} ${currentPage === page ? styles.pageBtnActive : ''}`}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}
            <button className={styles.pageBtn} onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}>
              Sau
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
