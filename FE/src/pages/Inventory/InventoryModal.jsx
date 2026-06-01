import React, { useState, useEffect } from 'react';
import { X } from '@phosphor-icons/react';
import styles from './Inventory.module.css';

export default function InventoryModal({ isOpen, onClose, initialData, onSuccess, productMap, warehouseMap }) {
  const [stockQuantity, setStockQuantity] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setStockQuantity(initialData.stock_quantity || 0);
      }
      setError('');
    }
  }, [isOpen, initialData]);

  if (!isOpen || !initialData) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (stockQuantity === '' || isNaN(stockQuantity)) {
      setError('Vui lòng nhập số lượng hợp lệ.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/inventory`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          id: initialData.id,
          warehouse_id: initialData.warehouse_id,
          stock_quantity: parseInt(stockQuantity)
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.[0]?.msg || data.detail || 'Có lỗi xảy ra');
      }

      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const productName = productMap[initialData.product_id] || `Sản phẩm #${initialData.product_id}`;
  const warehouseName = warehouseMap[initialData.warehouse_id] || `Kho #${initialData.warehouse_id}`;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Cập Nhật Tồn Kho</h3>
          <button className={styles.closeBtn} onClick={onClose} type="button">
            <X size={20} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Sản phẩm</label>
              <input
                type="text"
                className={styles.inputReadonly}
                value={productName}
                readOnly
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Kho hàng</label>
              <input
                type="text"
                className={styles.inputReadonly}
                value={warehouseName}
                readOnly
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Số lượng tồn</label>
              <input
                type="number"
                className={styles.input}
                placeholder="Nhập số lượng..."
                value={stockQuantity}
                onChange={(e) => setStockQuantity(e.target.value)}
                autoFocus
              />
              {error && <span className={styles.errorText}>{error}</span>}
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={loading}>
              Hủy
            </button>
            <button type="submit" className={styles.saveBtn} disabled={loading}>
              {loading ? 'Đang lưu...' : 'Lưu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
