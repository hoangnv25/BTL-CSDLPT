import React, { useState, useEffect } from 'react';
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';
import dayjs from 'dayjs';
import 'dayjs/locale/vi';

dayjs.locale('vi');

import Login from './pages/Login/Login';
import Sidebar from './components/Sidebar/Sidebar';
import Category from './pages/Category/Category';
import Product from './pages/Product/Product';
import Warehouse from './pages/Warehouse/Warehouse';
import Inventory from './pages/Inventory/Inventory';
import Order from './pages/Order/Order';
import Package from './pages/Package/Package';
import PackageWareHourse from './pages/PackageWareHourse/PackageWareHourse';
import MyOrder from './pages/MyOrder/MyOrder';
import ProductView from './pages/ProductView/ProductView';
import InventoryWareHourse from './pages/InventoryWareHourse/InventoryWareHourse';
import Stats from './pages/Stats/Stats';
import NotificationBell from './components/NotificationBell/NotificationBell';
import { roleAllowedPages } from './components/Sidebar/roles';

// Monkey patch fetch để tự động đính kèm Header định tuyến X-Target-Node
const originalFetch = window.fetch;
window.fetch = async function (...args) {
  let [resource, config] = args;
  // Chỉ thêm header nếu là gọi API tới Backend
  if (typeof resource === 'string' && (resource.includes('localhost') || resource.includes('127.0.0.1'))) {
    config = config || {};
    config.headers = {
      ...config.headers,
      'X-Target-Node': window.targetNode || 'main'
    };
    args[1] = config;
  }
  return originalFetch.apply(this, args);
};

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('order'); // Mặc định vào order để test
  const [warehouseRegionMap, setWarehouseRegionMap] = useState({});

  // State quản lý việc giả lập vai trò & kho
  const [currentOption, setCurrentOption] = useState('admin');

  // Khởi tạo bản đồ ánh xạ khu vực kho hàng để phục vụ Load Balancing
  useEffect(() => {
    originalFetch('http://localhost:8000/warehouse')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const mapping = {};
          data.forEach(wh => {
            mapping[wh.id] = wh.region.toLowerCase();
          });
          setWarehouseRegionMap(mapping);
        }
      })
      .catch(err => console.error("Không thể tải danh sách kho để phân luồng đọc:", err));
  }, []);

  // Phân tích role và warehouseId từ currentOption
  let role = 'admin';
  let warehouseId = 1; // Giá trị mặc định phòng hờ

  if (currentOption === 'user') {
    role = 'user';
    window.targetNode = 'auto'; // Load balancing ngẫu nhiên ở backend
  } else if (currentOption.startsWith('manager_')) {
    role = 'manager';
    warehouseId = parseInt(currentOption.split('_')[1], 10);
    // Tự động dò ra region của kho này từ bản đồ vừa tải
    window.targetNode = warehouseRegionMap[warehouseId] || 'main';
  } else {
    window.targetNode = 'main'; // Admin đọc từ main
  }

  // Khi thay đổi Vai trò/Kho, nếu activeTab không thuộc quyền truy cập của vai trò mới,
  // tự động nhảy sang tab đầu tiên được cho phép để tránh giao diện trống hoặc lỗi
  useEffect(() => {
    const allowed = roleAllowedPages[role] || [];
    if (!allowed.includes(activeTab)) {
      setActiveTab(allowed[0] || 'product_view');
    }
  }, [currentOption, role, activeTab]);

  useEffect(() => {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
      try {
        setCurrentUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Invalid user data in localStorage");
        localStorage.removeItem('currentUser');
      }
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setCurrentUser(userData);
    setActiveTab('order');
    setCurrentOption('admin'); // Reset về admin khi login
  };

  const handleLogout = () => {
    localStorage.removeItem('currentUser');
    setCurrentUser(null);
  };

  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'order':
        return <Order />;
      case 'stats':
        return <Stats warehouse_id={role === 'manager' ? warehouseId : null} />;
      case 'category':
        return <Category />;
      case 'product':
        return <Product />;
      case 'warehouse':
        return <Warehouse />;
      case 'inventory':
        return <Inventory />;
      case 'package':
        return <Package />;
      case 'package_warehouse':
        return <PackageWareHourse warehouse_id={warehouseId} key={`pkg-wh-${warehouseId}`} />;
      case 'my_order':
        return <MyOrder />;
      case 'product_view':
        return <ProductView />;
      case 'inventory_warehouse':
        return <InventoryWareHourse warehouse_id={warehouseId} key={`inv-wh-${warehouseId}`} />;
      default:
        return <div>Page Not Found</div>;
    }
  };

  return (
    <ConfigProvider locale={viVN}>
      <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg-main)' }}>
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          currentUser={currentUser}
          onLogout={handleLogout}
          currentOption={currentOption}
          onOptionChange={setCurrentOption}
        />
        <main style={{ flex: 1, overflowY: 'auto', padding: '2rem', position: 'relative' }}>
          {renderContent()}

          {/* Component Chuông và Drawer thông báo đồng bộ (Chỉ hiển thị với Admin tổng) */}
          {currentOption === 'admin' && <NotificationBell />}
        </main>
      </div>
    </ConfigProvider>
  );
}
export default App;
