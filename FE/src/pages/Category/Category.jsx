import React, { useState, useEffect } from 'react';
import { Plus, PencilSimple, Trash, ArrowsClockwise } from '@phosphor-icons/react';
import { message, Pagination } from 'antd';
import styles from './Category.module.css';
import CategoryModal from './CategoryModal';

export default function Category() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);

  // State quản lý Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  const fetchCategories = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/category`);
      if (!response.ok) throw new Error('Không thể tải danh sách danh mục');
      const data = await response.json();
      setCategories(data);
      setCurrentPage(1); // Reset page on fetch
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleOpenAdd = () => {
    setSelectedCategory(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (category) => {
    setSelectedCategory(category);
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa danh mục này?')) return;
    try {
      const response = await fetch(`${API_BASE_URL}/category/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Xóa thất bại');
      fetchCategories();
    } catch (err) {
      alert(err.message);
    }
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
      fetchCategories();
    } catch (err) {
      hide();
      message.error('Lỗi kết nối tới Backend khi thực hiện đồng bộ.');
    } finally {
      setSyncing(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    fetchCategories();
  };

  // Pagination Logic
  const totalPages = Math.ceil(categories.length / ITEMS_PER_PAGE) || 1;
  const currentData = categories.slice(
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
          Hiển thị {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, categories.length)} trong tổng số {categories.length} bản ghi
        </span>
        <Pagination
          current={currentPage}
          total={categories.length}
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
        <h1 className={styles.title}>Danh Mục Sản Phẩm</h1>
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
            Thêm danh mục
          </button>
        </div>
      </div>

      {error && <div style={{ color: 'var(--danger-color)', fontSize: '14px' }}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '10%' }}>ID</th>
                <th className={styles.th} style={{ width: '70%' }}>Tên Danh Mục</th>
                <th className={styles.th} style={{ width: '20%', textAlign: 'right' }}>Thao Tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="3" className={styles.emptyState}>Đang tải dữ liệu...</td>
                </tr>
              ) : currentData.length === 0 ? (
                <tr>
                  <td colSpan="3" className={styles.emptyState}>Chưa có danh mục nào.</td>
                </tr>
              ) : (
                currentData.map((cat) => (
                  <tr key={cat.id} className={styles.tableRow}>
                    <td className={styles.td}>{cat.id}</td>
                    <td className={styles.td}><strong>{cat.name}</strong></td>
                    <td className={styles.td}>
                      <div className={styles.actions} style={{ justifyContent: 'flex-end' }}>
                        <button
                          className={`${styles.actionBtn} ${styles.editBtn}`}
                          title="Sửa"
                          onClick={() => handleOpenEdit(cat)}
                        >
                          <PencilSimple size={16} weight="bold" />
                        </button>
                        <button
                          className={`${styles.actionBtn} ${styles.deleteBtn}`}
                          title="Xóa"
                          onClick={() => handleDelete(cat.id)}
                        >
                          <Trash size={16} weight="bold" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {!loading && categories.length > 0 && renderPagination()}
      </div>

      <CategoryModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        initialData={selectedCategory}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
