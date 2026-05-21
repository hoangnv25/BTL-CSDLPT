import React, { useState, useEffect } from 'react';
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

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('order'); // Mặc định vào order để test

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
      case 'category':
        return <Category />;
      case 'product':
        return <Product />;
      case 'warehouse':
        return <Warehouse />;
      case 'inventory':
        return <Inventory />;
      case 'order':
        return <Order />;
      case 'package':
        return <Package />;
      case 'package_warehouse':
        return <PackageWareHourse warehouse_id={1} />;
      case 'my_order':
        return <MyOrder />;
      case 'product_view':
        return <ProductView />;
      case 'inventory_warehouse':
        return <InventoryWareHourse warehouse_id={1} />;
      default:
        return <div>Page Not Found</div>;
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg-main)' }}>
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        currentUser={currentUser} 
        onLogout={handleLogout} 
      />
      
      <main style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
