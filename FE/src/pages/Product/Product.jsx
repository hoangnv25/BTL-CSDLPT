import React, { useState, useEffect } from 'react';
import { Plus, PencilSimple, Eye } from '@phosphor-icons/react';
import styles from './Product.module.css';
import ProductModal from './ProductModal';
import ProductDetailModal from './ProductDetailModal';

export default function Product() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // State quản lý Filter
  const [filterCategory, setFilterCategory] = useState('');
  const [filterWarehouse, setFilterWarehouse] = useState('');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  // State quản lý Modal Thêm/Sửa
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // State quản lý Modal Chi Tiết
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [detailProductId, setDetailProductId] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Lấy dữ liệu danh mục và kho một lần lúc khởi tạo
  const fetchMetadata = async () => {
    try {
      const [categoryRes, warehouseRes] = await Promise.all([
        fetch(`${API_BASE_URL}/category`),
        fetch(`${API_BASE_URL}/warehouse`)
      ]);
      if (categoryRes.ok) setCategories(await categoryRes.json());
      if (warehouseRes.ok) setWarehouses(await warehouseRes.json());
    } catch (err) {
      console.error("Lỗi lấy metadata:", err);
    }
  };

  // Fetch sản phẩm dựa trên filter
  const fetchProducts = async () => {
    setLoading(true);
    setError('');
    try {
      let endpoint = `${API_BASE_URL}/product`;
      
      if (filterCategory) {
        endpoint = `${API_BASE_URL}/product/by_category?category_id=${filterCategory}`;
      } else if (filterWarehouse) {
        endpoint = `${API_BASE_URL}/product/by_warehouse?warehouse_id=${filterWarehouse}`;
      }

      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Không thể tải danh sách sản phẩm');
      const data = await response.json();
      setProducts(data);
      setCurrentPage(1); // Reset page on fetch
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetadata();
  }, []);

  // Gọi fetchProducts mỗi khi filter thay đổi
  useEffect(() => {
    fetchProducts();
  }, [filterCategory, filterWarehouse]);

  // Handler Lọc Danh Mục (Reset Kho)
  const handleFilterCategoryChange = (e) => {
    const val = e.target.value;
    setFilterCategory(val);
    if (val) setFilterWarehouse(''); // Xóa filter Kho
  };

  // Handler Lọc Kho (Reset Danh Mục)
  const handleFilterWarehouseChange = (e) => {
    const val = e.target.value;
    setFilterWarehouse(val);
    if (val) setFilterCategory(''); // Xóa filter Danh Mục
  };

  const handleOpenAdd = () => {
    setSelectedProduct(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (product) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleOpenDetail = (id) => {
    setDetailProductId(id);
    setIsDetailOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const formatCurrency = (amount) => {
    if (!amount) return '0';
    return Number(amount).toLocaleString('vi-VN');
  };

  // Pagination Logic
  const totalPages = Math.ceil(products.length / ITEMS_PER_PAGE) || 1;
  const currentData = products.slice(
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
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, products.length)} trong tổng số {products.length} bản ghi
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
        <h1 className={styles.title}>Quản Lý Sản Phẩm</h1>
        <button className={styles.addBtn} onClick={handleOpenAdd}>
          <Plus size={16} weight="bold" />
          Thêm sản phẩm
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Danh mục:</label>
          <select 
            className={styles.filterSelect}
            value={filterCategory}
            onChange={handleFilterCategoryChange}
          >
            <option value="">-- Tất cả danh mục --</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        
        <div className={styles.filterGroup}>
          <label className={styles.filterLabel}>Kho hàng:</label>
          <select 
            className={styles.filterSelect}
            value={filterWarehouse}
            onChange={handleFilterWarehouseChange}
          >
            <option value="">-- Tất cả kho --</option>
            {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
        </div>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '10%' }}>ID</th>
                <th className={styles.th} style={{ width: '35%' }}>Tên Sản Phẩm</th>
                <th className={styles.th} style={{ width: '20%' }}>Danh Mục</th>
                <th className={styles.th} style={{ width: '15%', textAlign: 'right' }}>Giá Bán</th>
                <th className={styles.th} style={{ width: '10%', textAlign: 'center' }}>Tồn Kho</th>
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
                  <td colSpan="6" className={styles.emptyState}>Không tìm thấy sản phẩm nào phù hợp.</td>
                </tr>
              ) : (
                currentData.map((prod) => (
                  <tr key={prod.id} className={styles.tableRow}>
                    <td className={styles.td}>{prod.id}</td>
                    <td className={styles.td}><strong>{prod.name}</strong></td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      {prod.category_name || 'Không rõ'}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontWeight: '500' }}>
                      {formatCurrency(prod.price)}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'center' }}>
                      {prod.total_stock !== undefined ? prod.total_stock : prod.stock_quantity}
                    </td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button 
                          className={`${styles.actionBtn}`} 
                          title="Xem chi tiết"
                          onClick={() => handleOpenDetail(prod.id)}
                          style={{ color: 'var(--primary-color)' }}
                        >
                          <Eye size={16} weight="bold" />
                        </button>
                        <button 
                          className={`${styles.actionBtn} ${styles.editBtn}`} 
                          title="Sửa"
                          onClick={() => handleOpenEdit(prod)}
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
        {!loading && products.length > 0 && renderPagination()}
      </div>

      <ProductModal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal}
        initialData={selectedProduct}
        categories={categories}
        onSuccess={() => { setIsModalOpen(false); fetchProducts(); }}
      />
      
      <ProductDetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        productId={detailProductId}
      />
    </div>
  );
}
