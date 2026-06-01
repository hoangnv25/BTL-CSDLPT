import React, { useState, useEffect } from 'react';
import { Plus, PencilSimple, Eye, Trash, ArrowCounterClockwise, ArrowsClockwise } from '@phosphor-icons/react';
import { message, Modal, Pagination } from 'antd';
import styles from './Product.module.css';
import ProductModal from './ProductModal';
import ProductDetailModal from './ProductDetailModal';


export default function Product() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);
  
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
  const [detailProduct, setDetailProduct] = useState(null);

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
      let endpoint = `${API_BASE_URL}/product?include_deleted=true`;
      
      if (filterCategory) {
        endpoint = `${API_BASE_URL}/product/by_category?category_id=${filterCategory}&include_deleted=true`;
      } else if (filterWarehouse) {
        endpoint = `${API_BASE_URL}/product/by_warehouse?warehouse_id=${filterWarehouse}&include_deleted=true`;
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

  const showSyncFeedback = (data) => {
    if (!data.sync_results) return;

    const failedNodes = Object.entries(data.sync_results)
      .filter(([_, status]) => status === 'FAILED')
      .map(([node, _]) => node === 'north' ? 'Miền Bắc' : node === 'central' ? 'Miền Trung' : 'Miền Nam');

    if (failedNodes.length > 0) {
      message.warning({
        content: `Dữ liệu chính đã cập nhật, nhưng không thể đồng bộ tới: ${failedNodes.join(', ')}. Hệ thống sẽ tự động thử lại sau.`,
        duration: 5,
      });
    }
  };

  const handleOpenAdd = () => {
    setSelectedProduct(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (product) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleOpenDetail = (product) => {
    setDetailProduct(product);
    setDetailProductId(product.id);
    setIsDetailOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleModalSuccess = (data) => {
    setIsModalOpen(false);
    fetchProducts();
    const actionText = selectedProduct ? 'Cập nhật' : 'Thêm';
    message.success(`${actionText} sản phẩm thành công!`);
    showSyncFeedback(data);
  };

  const handleDeleteProduct = (id) => {
    Modal.confirm({
      title: 'Xác nhận xóa sản phẩm',
      content: 'Bạn có chắc chắn muốn xóa sản phẩm này không? (Sản phẩm sẽ bị ngừng kinh doanh)',
      okText: 'Xóa',
      okType: 'danger',
      cancelText: 'Hủy',
      onOk: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/product/${id}`, {
            method: 'DELETE',
          });
          if (!response.ok) throw new Error('Không thể xóa sản phẩm này.');
          const data = await response.json();
          message.success('Xóa sản phẩm thành công!');
          fetchProducts();
          showSyncFeedback(data);
        } catch (err) {
          message.error(err.message);
        }
      }
    });
  };

  const handleRestoreProduct = (id) => {
    Modal.confirm({
      title: 'Xác nhận khôi phục sản phẩm',
      content: 'Bạn có chắc chắn muốn khôi phục sản phẩm này không?',
      okText: 'Khôi phục',
      cancelText: 'Hủy',
      onOk: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/product/${id}/restore`, {
            method: 'POST',
          });
          if (!response.ok) throw new Error('Không thể khôi phục sản phẩm này.');
          const data = await response.json();
          message.success('Khôi phục sản phẩm thành công!');
          fetchProducts();
          showSyncFeedback(data);
        } catch (err) {
          message.error(err.message);
        }
      }
    });
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    const hide = message.loading('Đang đồng bộ dữ liệu tới các site nhánh...', 0);
    try {
      const nodes = ['north', 'central', 'south'];
      const successNodes = [];
      const failedNodes = [];

      for (const node of nodes) {
        try {
          const res = await fetch(`${API_BASE_URL}/replication/sync-node/${node}`);
          if (res.ok) {
            successNodes.push(node === 'central' ? 'Miền Trung' : node === 'north' ? 'Miền Bắc' : 'Miền Nam');
          } else {
            failedNodes.push(node === 'central' ? 'Miền Trung' : node === 'north' ? 'Miền Bắc' : 'Miền Nam');
          }
        } catch (e) {
          failedNodes.push(node === 'central' ? 'Miền Trung' : node === 'north' ? 'Miền Bắc' : 'Miền Nam');
        }
      }

      hide();
      if (failedNodes.length > 0) {
        message.warning(`Đồng bộ thành công: ${successNodes.join(', ') || 'Không có'}. Thất bại: ${failedNodes.join(', ')}`);
      } else {
        message.success(`Đã đồng bộ toàn bộ dữ liệu thành công tới: ${successNodes.join(', ')}`);
      }
      fetchProducts();
    } catch (err) {
      hide();
      message.error('Lỗi kết nối tới Backend khi thực hiện đồng bộ.');
    } finally {
      setSyncing(false);
    }
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
      <div className={styles.paginationContainer}>
        <span className={styles.pageInfo}>
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, products.length)} trong tổng số {products.length} bản ghi
        </span>
        <Pagination
          current={currentPage}
          total={products.length}
          pageSize={ITEMS_PER_PAGE}
          onChange={(page) => setCurrentPage(page)}
          showSizeChanger={false}
        />
      </div>
    );
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>Quản Lý Sản Phẩm</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className={styles.syncBtn}
            onClick={handleSyncAll}
            disabled={syncing}
          >
            <ArrowsClockwise size={16} weight="bold" className={syncing ? styles.spin : ''} />
            {syncing ? 'Đang đồng bộ...' : 'Đồng bộ hệ thống'}
          </button>
          <button className={styles.addBtn} onClick={handleOpenAdd}>
            <Plus size={16} weight="bold" />
            Thêm sản phẩm
          </button>
        </div>
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
                <th className={styles.th} style={{ width: '8%' }}>ID</th>
                <th className={styles.th} style={{ width: '40%' }}>Tên Sản Phẩm</th>
                <th className={styles.th} style={{ width: '15%' }}>Danh Mục</th>
                <th className={styles.th} style={{ width: '15%' }}>Trạng Thái</th>
                <th className={styles.th} style={{ width: '12%', textAlign: 'right' }}>Giá Bán</th>
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
                  <tr 
                    key={prod.id} 
                    className={styles.tableRow}
                    style={prod.deleted_at ? { opacity: 0.6, backgroundColor: '#f9f9f9' } : {}}
                  >
                    <td className={styles.td}>{prod.id}</td>
                    <td className={styles.td}>
                      <strong>{prod.name}</strong>
                      {prod.deleted_at && (
                        <span className={styles.deletedBadge} style={{
                          marginLeft: '8px',
                          fontSize: '10px',
                          backgroundColor: 'rgba(220, 53, 69, 0.1)',
                          color: '#dc3545',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontWeight: '600'
                        }}>Đã xóa</span>
                      )}
                    </td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      {prod.category_name || 'Không rõ'}
                    </td>
                    <td className={styles.td}>
                      {prod.deleted_at ? (
                        <span style={{ color: '#dc3545', fontWeight: '500', fontSize: '13px' }}>Ngừng bán</span>
                      ) : (
                        <span style={{ color: '#28a745', fontWeight: '500', fontSize: '13px' }}>Đang bán</span>
                      )}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontWeight: '500' }}>
                      {formatCurrency(prod.price)}
                    </td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button 
                          className={`${styles.actionBtn}`} 
                          title="Xem chi tiết"
                          onClick={() => handleOpenDetail(prod)}
                          style={{ color: 'var(--primary-color)' }}
                        >
                          <Eye size={16} weight="bold" />
                        </button>
                        {!prod.deleted_at ? (
                          <>
                            <button 
                              className={`${styles.actionBtn} ${styles.editBtn}`} 
                              title="Sửa"
                              onClick={() => handleOpenEdit(prod)}
                            >
                              <PencilSimple size={16} weight="bold" />
                            </button>
                            <button 
                              className={`${styles.actionBtn}`} 
                              title="Xóa"
                              onClick={() => handleDeleteProduct(prod.id)}
                              style={{ color: '#dc3545' }}
                            >
                              <Trash size={16} weight="bold" />
                            </button>
                          </>
                        ) : (
                          <button 
                            className={`${styles.actionBtn}`} 
                            title="Khôi phục"
                            onClick={() => handleRestoreProduct(prod.id)}
                            style={{ color: '#28a745' }}
                          >
                            <ArrowCounterClockwise size={16} weight="bold" />
                          </button>
                        )}
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
        onSuccess={handleModalSuccess}
      />
      
      <ProductDetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        productId={detailProductId}
        product={detailProduct}
      />
    </div>
  );
}
