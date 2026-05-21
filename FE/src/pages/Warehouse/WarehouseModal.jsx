import React, { useState, useEffect } from 'react';
import { X } from '@phosphor-icons/react';
import styles from './Warehouse.module.css';

const REGIONS = [
  { value: 'North', label: 'Miền Bắc' },
  { value: 'Central', label: 'Miền Trung' },
  { value: 'South', label: 'Miền Nam' }
];

export default function WarehouseModal({ isOpen, onClose, initialData, onSuccess }) {
  const [name, setName] = useState('');
  const [region, setRegion] = useState('North');
  const [address, setAddress] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const isEditMode = !!initialData;

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setName(initialData.name || '');
        setRegion(initialData.region || 'North');
        setAddress(initialData.address || '');
      } else {
        setName('');
        setRegion('North');
        setAddress('');
      }
      setError('');
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !address.trim()) {
      setError('Vui lòng điền đủ tên kho và địa chỉ.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const endpoint = isEditMode ? `/warehouse/${initialData.id}` : '/warehouse';
      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: name.trim(),
          region: region,
          address: address.trim()
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

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>
            {isEditMode ? 'Sửa Kho Hàng' : 'Thêm Kho Hàng Mới'}
          </h3>
          <button className={styles.closeBtn} onClick={onClose} type="button">
            <X size={20} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Tên kho hàng</label>
              <input
                type="text"
                className={styles.input}
                placeholder="Nhập tên kho..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Vùng miền</label>
              <select 
                className={styles.select}
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              >
                {REGIONS.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Địa chỉ</label>
              <input
                type="text"
                className={styles.input}
                placeholder="Nhập địa chỉ đầy đủ..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
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
