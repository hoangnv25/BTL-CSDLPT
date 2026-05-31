import React, { useState, useEffect } from 'react';
import { PencilSimple, MapPin } from '@phosphor-icons/react';
import styles from './Inventory.module.css';
import InventoryModal from './InventoryModal';
import { formatToVietnamTime } from '../../utils/dateTime';

export default function Inventory() {
  const [inventories, setInventories] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  
  // Hash maps for quick lookup
  const [productMap, setProductMap] = useState({});
  const [productCategoryMap, setProductCategoryMap] = useState({});
  const [warehouseMap, setWarehouseMap] = useState({});
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // State quản lý Filter
  const [filterWarehouse, setFilterWarehouse] = useState('');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  // State quản lý Modal Cập nhật
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedInventory, setSelectedInventory] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Tải metadata để hiển thị tên thay vì ID
  const fetchMetadata = async () => {
    try {
      const [productRes, warehouseRes] = await Promise.all([
        fetch(`${API_BASE_URL}/product`),
        fetch(`${API_BASE_URL}/warehouse`)
      ]);
      
      if (productRes.ok) {
        const pData = await productRes.json();
        const pMap = {};
        const pCatMap = {};
        pData.forEach(p => { 
          pMap[p.id] = p.name; 
          pCatMap[p.id] = p.category_name;
        });
        setProductMap(pMap);
        setProductCategoryMap(pCatMap);
      }
      
      if (warehouseRes.ok) {
        const wData = await warehouseRes.json();
        setWarehouses(wData);
        const wMap = {};
        wData.forEach(w => { wMap[w.id] = w.name; });
        setWarehouseMap(wMap);
      }
    } catch (err) {
      console.error("Lỗi lấy metadata:", err);
    }
  };

  // Fetch tồn kho dựa trên filter
  const fetchInventories = async () => {
    setLoading(true);
    setError('');
    try {
      let endpoint = `${API_BASE_URL}/inventory`;
      
      if (filterWarehouse) {
        endpoint = `${API_BASE_URL}/inventory/by_warehouse?warehouse_id=${filterWarehouse}`;
      }

      const response = await fetch(endpoint);
      if (!response.ok) throw new Error('Không thể tải danh sách tồn kho');
      const data = await response.json();
      setInventories(data);
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

  // Gọi fetchInventories mỗi khi filter thay đổi
  useEffect(() => {
    fetchInventories();
  }, [filterWarehouse]);

  const handleFilterWarehouseChange = (e) => {
    setFilterWarehouse(e.target.value);
  };

  const handleOpenEdit = (inventory) => {
    setSelectedInventory(inventory);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    fetchInventories(); // Load lại data
  };



  // Lọc chỉ giữ lại tồn kho của các sản phẩm còn đang hoạt động và sắp xếp theo warehouse_id, sau đó tới id
  const activeInventories = inventories
    .filter(inv => productMap[inv.product_id])
    .sort((a, b) => {
      if (a.warehouse_id !== b.warehouse_id) {
        return a.warehouse_id - b.warehouse_id;
      }
      return a.id - b.id;
    });

  // Pagination Logic
  const totalPages = Math.ceil(activeInventories.length / ITEMS_PER_PAGE) || 1;
  const currentData = activeInventories.slice(
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
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, activeInventories.length)} trong tổng số {activeInventories.length} bản ghi
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
        <h1 className={styles.title}>Quản Lý Tồn Kho</h1>
      </div>

      {/* Filter Toolbar */}
      <div className={styles.toolbar}>
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
                <th className={styles.th} style={{ width: '25%' }}>Sản Phẩm</th>
                <th className={styles.th} style={{ width: '15%' }}>Danh Mục</th>
                <th className={styles.th} style={{ width: '15%' }}>Kho Hàng</th>
                <th className={styles.th} style={{ width: '15%', textAlign: 'center' }}>Số Lượng Tồn</th>
                <th className={styles.th} style={{ width: '15%', textAlign: 'right' }}>Cập Nhật Cuối</th>
                <th className={styles.th} style={{ width: '7%', textAlign: 'right' }}>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="7" className={styles.emptyState}>Không có dữ liệu tồn kho.</td>
                </tr>
              ) : (
                currentData.map((inv) => (
                  <tr key={`${inv.warehouse_id}-${inv.id}`} className={styles.tableRow}>
                    <td className={styles.td}>{`${inv.warehouse_id}_${inv.id}`}</td>
                    <td className={styles.td}>
                      <strong>{productMap[inv.product_id] || `Sản phẩm #${inv.product_id}`}</strong>
                    </td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      {productCategoryMap[inv.product_id] || 'Không rõ'}
                    </td>
                    <td className={styles.td} style={{ color: 'var(--text-secondary)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <MapPin size={16} />
                        {warehouseMap[inv.warehouse_id] || `Kho #${inv.warehouse_id}`}
                      </div>
                    </td>
                    <td className={styles.td} style={{ textAlign: 'center', fontWeight: '500', color: 'var(--success-color)' }}>
                      {inv.stock_quantity}
                    </td>
                    <td className={styles.td} style={{ textAlign: 'right', fontSize: '13px', color: 'var(--text-secondary)' }}>
                      {formatToVietnamTime(inv.updated_at)}
                    </td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button 
                          className={`${styles.actionBtn} ${styles.editBtn}`} 
                          title="Cập nhật số lượng"
                          onClick={() => handleOpenEdit(inv)}
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
        {!loading && activeInventories.length > 0 && renderPagination()}
      </div>

      <InventoryModal 
        isOpen={isModalOpen} 
        onClose={handleCloseModal}
        initialData={selectedInventory}
        onSuccess={handleModalSuccess}
        productMap={productMap}
        warehouseMap={warehouseMap}
      />
    </div>
  );
}
