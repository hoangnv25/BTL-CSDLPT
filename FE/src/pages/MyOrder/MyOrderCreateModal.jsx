import React, { useState, useEffect } from 'react';
import { X, Plus, Trash } from '@phosphor-icons/react';
import styles from './MyOrder.module.css';

export default function MyOrderCreateModal({ isOpen, onClose, onSuccess }) {
  const [shippingAddress, setShippingAddress] = useState('');
  const [items, setItems] = useState([{ product_id: '', quantity: 1 }]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    if (isOpen) {
      setShippingAddress('');
      setItems([{ product_id: '', quantity: 1 }]);
      setError('');
      fetchProducts();
    }
  }, [isOpen]);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/product`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (err) {
      console.error("Lỗi lấy danh sách sản phẩm", err);
    }
  };

  const handleAddItem = () => {
    setItems([...items, { product_id: '', quantity: 1 }]);
  };

  const handleRemoveItem = (index) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate
    if (!shippingAddress.trim()) {
      setError('Vui lòng nhập địa chỉ giao hàng');
      return;
    }
    
    const validItems = items.filter(item => item.product_id && item.quantity > 0);
    if (validItems.length === 0) {
      setError('Vui lòng thêm ít nhất 1 sản phẩm với số lượng > 0');
      return;
    }
    
    // Format payload
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const userId = currentUser.id || 1; // Default fallback

    const payload = {
      user_id: userId,
      shipping_address: shippingAddress,
      items: validItems.map(i => ({
        product_id: parseInt(i.product_id),
        quantity: parseInt(i.quantity)
      }))
    };

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail?.[0]?.msg || errData.detail || 'Không thể tạo đơn hàng. Có thể do hết hàng trong kho.');
      }
      
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent} style={{ maxWidth: '600px' }}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Tạo Đơn Hàng Mới</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} weight="bold" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            {error && <div style={{ color: 'var(--danger-color)', marginBottom: '1rem', fontSize: '13px' }}>{error}</div>}

            <div className={styles.formGroup}>
              <label className={styles.label}>Địa chỉ giao hàng *</label>
              <textarea
                className={styles.textarea}
                value={shippingAddress}
                onChange={(e) => setShippingAddress(e.target.value)}
                placeholder="Nhập địa chỉ người nhận..."
                required
              />
            </div>

            <div className={styles.cartSection}>
              <div className={styles.cartHeader}>
                <h3>Giỏ Hàng</h3>
                <button type="button" className={styles.addBtn} onClick={handleAddItem} style={{ padding: '0.25rem 0.5rem', fontSize: '12px' }}>
                  <Plus size={14} weight="bold" /> Thêm SP
                </button>
              </div>

              <table className={styles.cartTable}>
                <thead>
                  <tr>
                    <th style={{ width: '60%' }}>Sản Phẩm</th>
                    <th style={{ width: '25%', textAlign: 'center' }}>Số Lượng</th>
                    <th style={{ width: '15%', textAlign: 'center' }}>Xóa</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, index) => (
                    <tr key={index}>
                      <td>
                        <select 
                          className={styles.productSelect}
                          value={item.product_id}
                          onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                          required
                        >
                          <option value="">-- Chọn Sản Phẩm --</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name} (Tồn: {p.total_stock || p.stock_quantity || 0})</option>
                          ))}
                        </select>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <input 
                          type="number" 
                          className={styles.quantityInput}
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                          min="1"
                          required
                        />
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {items.length > 1 && (
                          <button type="button" className={styles.removeBtn} onClick={() => handleRemoveItem(index)}>
                            <Trash size={16} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              * Hệ thống sẽ tự động phân bổ kiện hàng (Package) dựa trên thuật toán ưu tiên Kho có số lượng tồn nhiều nhất.
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button type="button" className={styles.btnCancel} onClick={onClose} disabled={loading}>
              Hủy
            </button>
            <button type="submit" className={styles.btnSubmit} disabled={loading}>
              {loading ? 'Đang tạo...' : 'Tạo Đơn Hàng'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
