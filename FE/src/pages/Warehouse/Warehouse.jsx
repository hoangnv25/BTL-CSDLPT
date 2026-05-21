import React, { useState, useEffect } from 'react';
import { Plus, PencilSimple } from '@phosphor-icons/react';
import styles from './Warehouse.module.css';
import WarehouseModal from './WarehouseModal';

const REGION_MAP = {
  'North': 'Miền Bắc',
  'Central': 'Miền Trung',
  'South': 'Miền Nam'
};

export default function Warehouse() {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // State quản lý Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/warehouse`);
      if (!response.ok) throw new Error('Không thể tải danh sách kho hàng');
      const data = await response.json();
      setWarehouses(data);
      setCurrentPage(1); // Reset page on fetch
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenAdd = () => {
    setSelectedWarehouse(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (warehouse) => {
    setSelectedWarehouse(warehouse);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    fetchData();
  };

  // Pagination Logic
  const totalPages = Math.ceil(warehouses.length / ITEMS_PER_PAGE) || 1;
  const currentData = warehouses.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(p => p - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(p => p + 1);
  };

  const renderPagination = () => {
    return (
      <div className={styles.pagination}>
        <span className={styles.pageInfo}>
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, warehouses.length)} trong tổng số {warehouses.length} bản ghi
        </span>
        <button className={styles.pageBtn} onClick={handlePrevPage} disabled={currentPage === 1}>
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
        <button className={styles.pageBtn} onClick={handleNextPage} disabled={currentPage === totalPages}>
          Sau
        </button>
      </div>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>Quản Lý Kho Hàng</h1>
        <button className={styles.addBtn} onClick={handleOpenAdd}>
          <Plus size={16} weight="bold" />
          Thêm kho hàng
        </button>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '10%' }}>ID</th>
                <th className={styles.th} style={{ width: '25%' }}>Tên Kho Hàng</th>
                <th className={styles.th} style={{ width: '15%' }}>Vùng Miền</th>
                <th className={styles.th} style={{ width: '40%' }}>Địa Chỉ</th>
                <th className={styles.th} style={{ width: '10%', textAlign: 'right' }}>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="5" className={styles.emptyState}>Chưa có kho hàng nào.</td>
                </tr>
              ) : (
                currentData.map((wh) => (
                  <tr key={wh.id} className={styles.tableRow}>
                    <td className={styles.td}>{wh.id}</td>
                    <td className={styles.td}><strong>{wh.name}</strong></td>
                    <td className={styles.td}>
                      {REGION_MAP[wh.region] || wh.region}
                    </td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      {wh.address}
                    </td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button 
                          className={`${styles.actionBtn} ${styles.editBtn}`} 
                          title="Sửa"
                          onClick={() => handleOpenEdit(wh)}
                        >
                          <PencilSimple size={16} weight="bold" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && warehouses.length > 0 && renderPagination()}
      </div>

      <WarehouseModal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal}
        initialData={selectedWarehouse}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
