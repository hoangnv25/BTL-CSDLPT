import React, { useState, useEffect } from 'react';
import { X, Package as PackageIcon } from '@phosphor-icons/react';
import styles from './Order.module.css';
import { formatToVietnamTime } from '../../utils/dateTime';

export default function OrderDetailModal({ isOpen, onClose, orderId }) {
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingPackageId, setUpdatingPackageId] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    if (isOpen && orderId) {
      fetchOrderDetail();
    }
  }, [isOpen, orderId]);

  const fetchOrderDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/order/${orderId}`);
      if (!response.ok) throw new Error('Không thể tải chi tiết đơn hàng');
      const data = await response.json();
      setOrder(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePackageStatus = async (packageId, newStatus) => {
    setUpdatingPackageId(packageId);
    try {
      const response = await fetch(`${API_BASE_URL}/package/${packageId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) throw new Error('Không thể cập nhật trạng thái kiện hàng');
      
      // Cập nhật state cục bộ để giao diện phản hồi nhanh
      setOrder(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          packages: prev.packages.map(pkg => 
            pkg.package_id === packageId ? { ...pkg, status: newStatus } : pkg
          )
        };
      });
    } catch (err) {
      alert(err.message);
    } finally {
      setUpdatingPackageId(null);
    }
  };

  if (!isOpen) return null;

  const formatCurrency = (amount) => {
    if (!amount) return '0';
    return Number(amount).toLocaleString('vi-VN') + ' đ';
  };



  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Chi Tiết Đơn Hàng #{orderId}</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} weight="bold" />
          </button>
        </div>

        <div className={styles.modalBody}>
          {loading ? (
            <div className={styles.emptyState}>Đang tải chi tiết đơn hàng...</div>
          ) : error ? (
            <div style={{ color: 'var(--danger-color)' }}>{error}</div>
          ) : order ? (
            <>
              {/* Thông tin chung */}
              <div className={styles.detailGrid}>
                <div>
                  <div className={styles.detailItem}>
                    <span>Khách hàng:</span>
                    <strong>{order.user?.full_name || order.user?.username}</strong>
                  </div>
                  <div className={styles.detailItem}>
                    <span>Ngày đặt:</span>
                    <strong>{formatToVietnamTime(order.ordered_at)}</strong>
                  </div>
                </div>
                <div>
                  <div className={styles.detailItem}>
                    <span>Địa chỉ giao:</span>
                    <strong>{order.shipping_address}</strong>
                  </div>
                  <div className={styles.detailItem}>
                    <span>Tổng tiền:</span>
                    <strong style={{ color: 'var(--primary-color)', fontSize: '16px' }}>
                      {formatCurrency(order.total_amount)}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Danh sách Package (Kiện hàng) */}
              <h3 style={{ fontSize: '16px', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                Phân bổ kiện hàng ({order.packages?.length || 0} kiện)
              </h3>
              
              {order.packages && order.packages.length > 0 ? (
                order.packages.map((pkg, index) => (
                  <div key={pkg.package_id || index} className={styles.packageCard}>
                    <div className={styles.packageHeader}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <PackageIcon size={18} weight="fill" color="var(--primary-color)" />
                        <h4>Kiện hàng từ: {pkg.warehouse?.name || 'Kho không xác định'}</h4>
                      </div>
                        <select
                        value={pkg.status || 'Pending'}
                        onChange={(e) => handleUpdatePackageStatus(pkg.package_id, e.target.value)}
                        disabled={updatingPackageId === pkg.package_id}
                        className={`${styles.packageBadgeSelect} ${styles[`status${pkg.status || 'Pending'}`]}`}
                      >
                        <option value="Pending">Pending</option>
                        <option value="Shipping">Shipping</option>
                        <option value="Delivered">Delivered</option>
                      </select>
                    </div>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th className={styles.th} style={{ padding: '0.5rem 1rem' }}>Tên Sản Phẩm</th>
                          <th className={styles.th} style={{ padding: '0.5rem 1rem', textAlign: 'center' }}>Số Lượng</th>
                          <th className={styles.th} style={{ padding: '0.5rem 1rem', textAlign: 'right' }}>Đơn Giá</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pkg.items && pkg.items.map((item, idx) => (
                          <tr key={idx}>
                            <td className={styles.td} style={{ padding: '0.5rem 1rem' }}>{item.product?.name}</td>
                            <td className={styles.td} style={{ padding: '0.5rem 1rem', textAlign: 'center', fontWeight: '500' }}>
                              {item.quantity}
                            </td>
                            <td className={styles.td} style={{ padding: '0.5rem 1rem', textAlign: 'right' }}>
                              {formatCurrency(item.product?.price)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))
              ) : (
                <div className={styles.emptyState}>Không có kiện hàng nào.</div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
