import React, { useState, useEffect } from 'react';
import { ShoppingBag, ChartLineUp, Storefront, ArrowsClockwise } from '@phosphor-icons/react';
import { message } from 'antd';
import dayjs from 'dayjs';
import styles from './Stats.module.css';

export default function Stats({ warehouse_id = null }) {
  const [loading, setLoading] = useState(false);
  const [topProducts, setTopProducts] = useState([]);
  const [revenueData, setRevenueData] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  
  // Filters
  const [period, setPeriod] = useState('month');
  const [warehouseId, setWarehouseId] = useState(warehouse_id);
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [selectedMonth, setSelectedMonth] = useState(dayjs().format('YYYY-MM'));

  // Pagination for Top Products
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    setWarehouseId(warehouse_id);
  }, [warehouse_id]);

  useEffect(() => {
    fetchWarehouses();
  }, []);

  useEffect(() => {
    fetchStats();
  }, [period, warehouseId, selectedDate, selectedMonth]);

  const fetchWarehouses = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/warehouse`);
      if (res.ok) {
        const data = await res.json();
        setWarehouses(data);
      }
    } catch (err) {
      console.error("Lỗi lấy danh sách kho:", err);
    }
  };

  const fetchStats = async () => {
    setLoading(true);
    try {
      let queryParams = `period=${period}`;
      if (warehouseId) queryParams += `&warehouse_id=${warehouseId}`;
      
      if (period === 'day' && selectedDate) {
        queryParams += `&specific_date=${selectedDate}`;
      } else if (period === 'month') {
        const [year, month] = selectedMonth.split('-');
        queryParams += `&specific_month=${parseInt(month)}&specific_year=${year}`;
      } else if (period === 'year' && selectedDate) {
        queryParams += `&specific_year=${dayjs(selectedDate).year()}`;
      }

      // Fetch Top Products
      const topRes = await fetch(`${API_BASE_URL}/stats/top-products?${queryParams}`);
      const topData = await topRes.json();
      setTopProducts(Array.isArray(topData) ? topData : []);
      setCurrentPage(1);

      // Fetch Revenue
      const revRes = await fetch(`${API_BASE_URL}/stats/revenue?${queryParams}`);
      const revData = await revRes.json();
      setRevenueData(revData);

    } catch (err) {
      console.error("Error fetching stats:", err);
      message.error("Lỗi khi tải dữ liệu thống kê");
    } finally {
      setLoading(false);
    }
  };

  const handleManualSync = async () => {
    const hide = message.loading('Đang cập nhật dữ liệu...', 0);
    setLoading(true);
    try {
      let queryParams = '';
      if (period === 'day' && selectedDate) {
        queryParams = `specific_date=${selectedDate}`;
      } else if (period === 'month' && selectedMonth) {
        const [year, month] = selectedMonth.split('-');
        queryParams = `specific_month=${parseInt(month)}&specific_year=${year}`;
      } else if (period === 'year' && selectedDate) {
        queryParams = `specific_year=${dayjs(selectedDate).year()}`;
      }

      const url = queryParams 
        ? `${API_BASE_URL}/stats/sync?${queryParams}` 
        : `${API_BASE_URL}/stats/sync`;

      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      hide();
      if (res.ok) {
        message.success(data.message || "Cập nhật thành công!");
        fetchStats();
      } else {
        message.error(data.detail || "Lỗi cập nhật");
      }
    } catch (err) {
      hide();
      console.error("Lỗi cập nhật:", err);
      message.error("Lỗi kết nối máy chủ");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
  };

  // Pagination logic
  const totalItems = topProducts.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedProducts = topProducts.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const months = [
    { label: 'Tháng 1', value: '01' }, { label: 'Tháng 2', value: '02' },
    { label: 'Tháng 3', value: '03' }, { label: 'Tháng 4', value: '04' },
    { label: 'Tháng 5', value: '05' }, { label: 'Tháng 6', value: '06' },
    { label: 'Tháng 7', value: '07' }, { label: 'Tháng 8', value: '08' },
    { label: 'Tháng 9', value: '09' }, { label: 'Tháng 10', value: '10' },
    { label: 'Tháng 11', value: '11' }, { label: 'Tháng 12', value: '12' },
  ];

  const years = Array.from({ length: 11 }, (_, i) => dayjs().year() - 10 + i).reverse();

  const getDaysInMonth = (year, month) => {
    return dayjs(`${year}-${month}-01`).daysInMonth();
  };

  // Lấy thông tin kho hiện tại từ danh mục warehouses
  const currentWarehouse = warehouses.find(w => Number(w.id) === Number(warehouseId));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          Thống Kê 
          {currentWarehouse ? ` - ${currentWarehouse.name}` : (warehouseId ? '' : ' - Toàn Hệ Thống')}
        </h2>
        
        <div className={styles.filterBar}>
          {!warehouse_id && (
            <select 
              className={styles.select}
              onChange={(e) => setWarehouseId(e.target.value ? Number(e.target.value) : null)}
              value={warehouseId || ''}
            >
              <option value="">Toàn hệ thống</option>
              {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          )}
          
          <div className={styles.inputGroup}>
            <select 
              className={styles.select}
              value={period} 
              onChange={(e) => {
                const newPeriod = e.target.value;
                setPeriod(newPeriod);
                if (newPeriod === 'day') setSelectedDate(dayjs().format('YYYY-MM-DD'));
                if (newPeriod === 'month') setSelectedMonth(dayjs().format('YYYY-MM'));
                if (newPeriod === 'year') setSelectedDate(dayjs().format('YYYY-MM-DD'));
                setCurrentPage(1);
              }}
            >
              <option value="day">Theo Ngày</option>
              <option value="month">Theo Tháng</option>
              <option value="year">Theo Năm</option>
            </select>

            {period === 'day' && (
              <>
                <select 
                  className={styles.select}
                  value={dayjs(selectedDate).date()}
                  onChange={(e) => {
                    const newDate = dayjs(selectedDate).date(e.target.value).format('YYYY-MM-DD');
                    setSelectedDate(newDate);
                  }}
                >
                  {Array.from({ length: getDaysInMonth(dayjs(selectedDate).year(), dayjs(selectedDate).month() + 1) }, (_, i) => (
                    <option key={i + 1} value={i + 1}>{i + 1}</option>
                  ))}
                </select>
                <select 
                  className={styles.select}
                  value={dayjs(selectedDate).format('MM')}
                  onChange={(e) => {
                    const newDate = dayjs(selectedDate).month(parseInt(e.target.value) - 1).format('YYYY-MM-DD');
                    setSelectedDate(newDate);
                  }}
                >
                  {months.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
                <select 
                  className={styles.select}
                  value={dayjs(selectedDate).year()}
                  onChange={(e) => {
                    const newDate = dayjs(selectedDate).year(e.target.value).format('YYYY-MM-DD');
                    setSelectedDate(newDate);
                  }}
                >
                  {years.map(y => (
                    <option key={y} value={y}>Năm {y}</option>
                  ))}
                </select>
              </>
            )}

            {period === 'month' && (
              <>
                <select 
                  className={styles.select}
                  value={selectedMonth.split('-')[1]}
                  onChange={(e) => setSelectedMonth(`${selectedMonth.split('-')[0]}-${e.target.value}`)}
                >
                  {months.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
                <select 
                  className={styles.select}
                  value={selectedMonth.split('-')[0]}
                  onChange={(e) => setSelectedMonth(`${e.target.value}-${selectedMonth.split('-')[1]}`)}
                >
                  {years.map(y => (
                    <option key={y} value={y}>Năm {y}</option>
                  ))}
                </select>
              </>
            )}

            {period === 'year' && (
              <select 
                className={styles.select}
                value={dayjs(selectedDate).year()}
                onChange={(e) => setSelectedDate(dayjs().year(e.target.value).format('YYYY-MM-DD'))}
              >
                {years.map(y => (
                  <option key={y} value={y}>Năm {y}</option>
                ))}
              </select>
            )}
          </div>

          <button 
            className={styles.syncBtn}
            onClick={handleManualSync}
            disabled={loading}
          >
            <ArrowsClockwise size={18} weight="bold" className={loading ? styles.spinning : ''} />
            <span>Cập nhật</span>
          </button>
        </div>
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={`${styles.iconWrapper} ${styles.revenueIcon}`}>
            <ChartLineUp size={24} weight="bold" />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>Tổng Doanh Thu</span>
            <span className={styles.statValue}>{formatCurrency(revenueData?.total_revenue)}</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={`${styles.iconWrapper} ${styles.packageIcon}`}>
            <ShoppingBag size={24} weight="bold" />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>Tổng Kiện Hàng</span>
            <span className={styles.statValue}>{revenueData?.total_packages || 0}</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={`${styles.iconWrapper} ${styles.regionIcon}`}>
            <Storefront size={24} weight="bold" />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>Khu Vực</span>
            <span className={styles.statValue}>
              {currentWarehouse ? currentWarehouse.name : "Toàn quốc"}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <h3 className={styles.tableTitle}>Top 10 Sản Phẩm Bán Chạy</h3>
        </div>
        
        <div className={styles.tableContainer}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th} style={{ width: '80px' }}>Hạng</th>
                <th className={styles.th}>Sản phẩm</th>
                <th className={styles.th}>Đơn giá</th>
                <th className={styles.th}>Đã bán</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" className={styles.loadingCell}>Đang tải dữ liệu...</td>
                </tr>
              ) : paginatedProducts.length > 0 ? (
                paginatedProducts.map((p, index) => (
                  <tr key={p.product_id} className={styles.tableRow}>
                    <td className={styles.td}>
                      <span className={`${styles.rankTag} ${index + startIndex < 3 ? styles.topRank : ''}`}>
                        {index + startIndex + 1}
                      </span>
                    </td>
                    <td className={styles.td}>
                      <span className={styles.productName}>{p.product_name}</span>
                    </td>
                    <td className={styles.td}>{formatCurrency(p.price)}</td>
                    <td className={`${styles.td} ${styles.soldCount}`}>
                      {p.total_sold}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className={styles.emptyCell}>Không có dữ liệu trong khoảng thời gian này</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className={styles.pagination}>
            <div className={styles.paginationInfo}>
              Hiển thị {startIndex + 1} - {Math.min(startIndex + ITEMS_PER_PAGE, totalItems)} trong tổng số {totalItems}
            </div>
            <div className={styles.pageActions}>
              <button 
                className={styles.pageBtn} 
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => prev - 1)}
              >
                Trước
              </button>
              {[...Array(totalPages)].map((_, i) => (
                <button 
                  key={i + 1}
                  className={`${styles.pageBtn} ${currentPage === i + 1 ? styles.pageBtnActive : ''}`}
                  onClick={() => setCurrentPage(i + 1)}
                >
                  {i + 1}
                </button>
              ))}
              <button 
                className={styles.pageBtn} 
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                Sau
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
