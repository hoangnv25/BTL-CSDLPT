import React, { useState, useEffect } from 'react';
import { Plus, Eye } from '@phosphor-icons/react';
import styles from './MyOrder.module.css';
import MyOrderCreateModal from './MyOrderCreateModal';
import MyOrderDetailModal from './MyOrderDetailModal';

export default function MyOrder() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  // State quản lý Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Lấy currentUser
  const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
  const userId = currentUser.id;

  const fetchOrders = async () => {
    if (!userId) {
      setError('Bạn cần đăng nhập để xem đơn hàng của mình');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/order/my?user_id=${userId}`);
      if (!response.ok) throw new Error('Không thể tải danh sách đơn hàng của tôi');
      const data = await response.json();
      const sortedData = data.sort((a, b) => new Date(b.ordered_at) - new Date(a.ordered_at));
      setOrders(sortedData);
      setCurrentPage(1); // Reset page on fetch
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [userId]);

  const handleOpenCreate = () => {
    setIsCreateOpen(true);
  };

  const handleOpenDetail = (id) => {
    setSelectedOrderId(id);
    setIsDetailOpen(true);
  };

  const handleCreateSuccess = () => {
    setIsCreateOpen(false);
    fetchOrders();
  };

  const formatCurrency = (amount) => {
    if (!amount) return '0';
    return Number(amount).toLocaleString('vi-VN') + ' đ';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('vi-VN');
  };

  // Pagination Logic
  const totalPages = Math.ceil(orders.length / ITEMS_PER_PAGE) || 1;
  const currentData = orders.slice(
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
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, orders.length)} trong tổng số {orders.length} bản ghi
        </span>
        <button 
          className={styles.pageBtn} 
          onClick={handlePrevPage} 
          disabled={currentPage === 1}
        >
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
        <button 
          className={styles.pageBtn} 
          onClick={handleNextPage} 
          disabled={currentPage === totalPages}
        >
          Sau
        </button>
      </div>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>Đơn Hàng Của Tôi</h1>
        <button className={styles.addBtn} onClick={handleOpenCreate}>
          <Plus size={16} weight="bold" />
          Tạo đơn hàng mới
        </button>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px', marginBottom: '1rem' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '8%' }}>ID</th>
                <th className={styles.th} style={{ width: '25%' }}>Khách Hàng</th>
                <th className={styles.th} style={{ width: '25%' }}>Địa Chỉ Giao</th>
                <th className={styles.th} style={{ width: '15%', textAlign: 'right' }}>Tổng Tiền</th>
                <th className={styles.th} style={{ width: '17%', textAlign: 'right' }}>Ngày Đặt</th>
                <th className={styles.th} style={{ width: '10%', textAlign: 'right' }}>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="6" className={styles.emptyState}>Bạn chưa có đơn hàng nào.</td>
                </tr>
              ) : (
                currentData.map((order) => (
                  <tr key={order.order_id} className={styles.tableRow}>
                    <td className={styles.td}>#{order.order_id}</td>
                    <td className={styles.td}>
                      <strong>{order.user?.full_name || order.user?.username}</strong>
                    </td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      {order.shipping_address}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontWeight: '600', color: 'var(--primary-color)' }}>
                      {formatCurrency(order.total_amount)}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontSize: '13px', color: 'var(--text-secondary)' }}>
                      {formatDate(order.ordered_at)}
                    </td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button 
                          className={`${styles.actionBtn}`} 
                          title="Xem chi tiết"
                          onClick={() => handleOpenDetail(order.order_id)}
                          style={{ color: 'var(--primary-color)' }}
                        >
                          <Eye size={18} weight="bold" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && orders.length > 0 && renderPagination()}
      </div>

      <MyOrderCreateModal 
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      <MyOrderDetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        orderId={selectedOrderId}
      />
    </div>
  );
}
