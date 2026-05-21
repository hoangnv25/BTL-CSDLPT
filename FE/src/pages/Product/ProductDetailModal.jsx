import React, { useState, useEffect } from 'react';
import { X, MapPin } from '@phosphor-icons/react';
import styles from './Product.module.css';

export default function ProductDetailModal({ isOpen, onClose, productId }) {
  const [productDetail, setProductDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    if (isOpen && productId) {
      fetchDetail();
    }
  }, [isOpen, productId]);

  const fetchDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/product/${productId}`);
      if (!response.ok) throw new Error('Không thể tải chi tiết sản phẩm');
      const data = await response.json();
      setProductDetail(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatCurrency = (amount) => {
    if (!amount) return '0';
    return Number(amount).toLocaleString('vi-VN');
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('vi-VN');
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} style={{ maxWidth: '600px' }}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Chi Tiết Sản Phẩm</h3>
          <button className={styles.closeBtn} onClick={onClose} type="button">
            <X size={20} weight="bold" />
          </button>
        </div>

        <div className={styles.modalBody}>
          {loading ? (
            <div className={styles.emptyState}>Đang tải dữ liệu...</div>
          ) : error ? (
            <div className={styles.errorText}>{error}</div>
          ) : productDetail ? (
            <>
              {/* Thông tin cơ bản */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                  {productDetail.name}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '14px' }}>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Danh mục: </span>
                    <strong style={{ color: 'var(--text-primary)' }}>{productDetail.category_name || 'Không rõ'}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Giá bán: </span>
                    <strong style={{ color: 'var(--primary-color)' }}>{formatCurrency(productDetail.price)} VNĐ</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-secondary)' }}>Tổng tồn kho: </span>
                    <strong style={{ color: 'var(--success-color)' }}>{productDetail.total_stock}</strong>
                  </div>
                </div>
              </div>

              {/* Bảng tồn kho từng kho */}
              <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '0.5rem', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>Tồn Kho Tại Các Kho</h4>
              <div style={{ border: '1px solid var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
                <table className={styles.table} style={{ margin: 0 }}>
                  <thead>
                    <tr>
                      <th className={styles.th} style={{ padding: '0.5rem 1rem' }}>Kho Hàng</th>
                      <th className={styles.th} style={{ padding: '0.5rem 1rem', textAlign: 'center' }}>Số Lượng</th>
                      <th className={styles.th} style={{ padding: '0.5rem 1rem', textAlign: 'right' }}>Cập Nhật Cuối</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(!productDetail.inventory || productDetail.inventory.length === 0) ? (
                      <tr>
                        <td colSpan="3" className={styles.emptyState} style={{ padding: '1.5rem' }}>Chưa có hàng trong bất kỳ kho nào.</td>
                      </tr>
                    ) : (
                      productDetail.inventory.map((inv) => (
                        <tr key={inv.id} className={styles.tableRow}>
                          <td className={styles.td} style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <MapPin size={16} color="var(--text-secondary)" />
                            {inv.warehouse_name}
                          </td>
                          <td className={styles.td} style={{ padding: '0.5rem 1rem', textAlign: 'center', fontWeight: '500' }}>
                            {inv.stock_quantity}
                          </td>
                          <td className={styles.td} style={{ padding: '0.5rem 1rem', textAlign: 'right', color: 'var(--text-secondary)', fontSize: '13px' }}>
                            {formatDate(inv.updated_at)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </div>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.cancelBtn} onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}
