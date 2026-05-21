import React, { useState, useEffect } from 'react';
import { X } from '@phosphor-icons/react';
import styles from './Product.module.css';

export default function ProductModal({ isOpen, onClose, initialData, categories, onSuccess }) {
  const [name, setName] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [price, setPrice] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
  const isEditMode = !!initialData;

  useEffect(() => {
    if (isOpen) {
      if (initialData) {
        setName(initialData.name || '');
        setCategoryId(initialData.category_id || '');
        setPrice(initialData.price || '');
      } else {
        setName('');
        setCategoryId(categories.length > 0 ? categories[0].id : '');
        setPrice('');
      }
      setError('');
    }
  }, [isOpen, initialData, categories]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !categoryId || !price) {
      setError('Vui lòng điền đầy đủ thông tin.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const endpoint = isEditMode ? `/product/${initialData.id}` : '/product';
      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: name.trim(),
          category_id: parseInt(categoryId),
          price: parseFloat(price)
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
            {isEditMode ? 'Sửa Sản Phẩm' : 'Thêm Sản Phẩm Mới'}
          </h3>
          <button className={styles.closeBtn} onClick={onClose} type="button">
            <X size={20} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Tên sản phẩm</label>
              <input
                type="text"
                className={styles.input}
                placeholder="Nhập tên sản phẩm..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Danh mục</label>
              <select 
                className={styles.select}
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
              >
                <option value="" disabled>Chọn danh mục</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Giá bán</label>
              <input
                type="number"
                step="0.01"
                className={styles.input}
                placeholder="Nhập giá bán..."
                value={price}
                onChange={(e) => setPrice(e.target.value)}
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
