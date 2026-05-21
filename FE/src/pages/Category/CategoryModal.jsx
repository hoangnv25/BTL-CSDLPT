import React, { useState, useEffect } from 'react';
import { X } from '@phosphor-icons/react';
import styles from './Category.module.css';

export default function CategoryModal({ isOpen, onClose, initialData, onSuccess }) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const isEditMode = !!initialData;

  useEffect(() => {
    if (isOpen) {
      setName(initialData ? initialData.name : '');
      setError('');
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Vui lòng nhập tên danh mục.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const endpoint = isEditMode ? `/category/${initialData.id}` : '/category';
      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.[0]?.msg || data.detail || 'Có lỗi xảy ra');
      }

      onSuccess(); // Đóng modal và tải lại danh sách
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
            {isEditMode ? 'Sửa Danh Mục' : 'Thêm Danh Mục Mới'}
          </h3>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Tên danh mục</label>
              <input
                type="text"
                className={styles.input}
                placeholder="Nhập tên danh mục..."
                value={name}
                onChange={(e) => setName(e.target.value)}
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
