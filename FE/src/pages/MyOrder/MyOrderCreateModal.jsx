import React, { useState, useEffect } from 'react';
import { X, Plus, Trash } from '@phosphor-icons/react';
import styles from './MyOrder.module.css';

export default function MyOrderCreateModal({ isOpen, onClose, onSuccess }) {
  const [shippingAddress, setShippingAddress] = useState('');
  const [items, setItems] = useState([{ product_id: '', quantity: 1 }]);
  const [products, setProducts] = useState([]);
  const [productStockMap, setProductStockMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    if (isOpen) {
      setShippingAddress('');
      setItems([{ product_id: '', quantity: 1 }]);
      setProductStockMap({});
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

  const fetchProductStock = async (productId) => {
    if (!productId || productStockMap[productId] !== undefined) return;
    try {
      const response = await fetch(`${API_BASE_URL}/product/${productId}`);
      if (response.ok) {
        const data = await response.json();
        setProductStockMap(prev => ({
          ...prev,
          [productId]: data.total_stock
        }));
      }
    } catch (err) {
      console.error("Lỗi lấy tồn kho sản phẩm:", err);
    }
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    setItems(newItems);

    if (field === 'product_id' && value) {
      fetchProductStock(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate
    if (!shippingAddress.trim()) {
      setError('Vui lòng nhập địa chỉ giao hàng');
      return;
    }
    
    // Cho phép gửi mọi số lượng (kể cả <= 0) lên BE để test validation của BE
    const validItems = items.filter(item => item.product_id);
    if (validItems.length === 0) {
      setError('Vui lòng chọn ít nhất 1 sản phẩm');
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
        quantity: isNaN(parseInt(i.quantity)) ? i.quantity : parseInt(i.quantity)
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
                <button type="button" className={styles.addBtn} onClick={handleAddItem}>
                  <Plus size={14} weight="bold" /> Thêm SP
                </button>
              </div>

              <div className={styles.cartItemsList}>
                {items.map((item, index) => {
                  const stock = productStockMap[item.product_id];
                  let stockBadgeClass = styles.stockLoading;
                  let stockText = 'Đang kiểm tra tồn kho...';
                  
                  if (item.product_id && stock !== undefined) {
                    if (stock === 0) {
                      stockBadgeClass = styles.stockEmpty;
                      stockText = 'Hết hàng';
                    } else if (stock <= 5) {
                      stockBadgeClass = styles.stockWarning;
                      stockText = `Tồn kho hạn chế: ${stock}`;
                    } else {
                      stockBadgeClass = styles.stockAvailable;
                      stockText = `Tồn kho khả dụng: ${stock}`;
                    }
                  }

                  return (
                    <div key={index} className={styles.cartItemRow}>
                      <div className={styles.productSelectorCol}>
                        <label className={styles.label} style={{ marginBottom: '4px', fontSize: '11px', fontWeight: '500' }}>
                          Sản phẩm {items.length > 1 ? `#${index + 1}` : ''}
                        </label>
                        <select 
                          className={styles.productSelect}
                          value={item.product_id}
                          onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                          required
                          style={{ height: '36px', padding: '0.4rem 0.75rem', fontSize: '14px' }}
                        >
                          <option value="">-- Chọn Sản Phẩm --</option>
                          {products.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                          ))}
                        </select>
                        {item.product_id && (
                          <span className={`${styles.stockBadge} ${stockBadgeClass}`}>
                            {stockText}
                          </span>
                        )}
                      </div>
                      
                      <div className={styles.quantitySelectorCol}>
                        <label className={styles.label} style={{ marginBottom: '4px', fontSize: '11px', fontWeight: '500' }}>
                          Số lượng
                        </label>
                        <div className={styles.quantityControlGroup}>
                          <button 
                            type="button" 
                            className={styles.qtyBtn}
                            onClick={() => handleItemChange(index, 'quantity', (parseInt(item.quantity) || 0) - 1)}
                          >
                            -
                          </button>
                          <input 
                            type="number" 
                            className={styles.qtyInput}
                            value={item.quantity}
                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                          />
                          <button 
                            type="button" 
                            className={styles.qtyBtn}
                            onClick={() => handleItemChange(index, 'quantity', (parseInt(item.quantity) || 0) + 1)}
                          >
                            +
                          </button>
                        </div>
                      </div>

                      <div className={styles.deleteActionCol}>
                        {items.length > 1 && (
                          <button 
                            type="button" 
                            className={styles.trashBtn} 
                            onClick={() => handleRemoveItem(index)}
                            title="Xóa sản phẩm"
                          >
                            <Trash size={18} weight="bold" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
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
