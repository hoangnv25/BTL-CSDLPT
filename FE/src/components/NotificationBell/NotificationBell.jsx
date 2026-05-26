import React, { useState, useEffect } from 'react';
import { notification } from 'antd';
import { Bell, X } from '@phosphor-icons/react';
import styles from './NotificationBell.module.css';

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState(() => {
    const saved = localStorage.getItem('sync_notifications');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    let ws;
    const connectWebSocket = () => {
      ws = new WebSocket('ws://localhost:8000/ws/notifications');
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Lưu vào lịch sử
          const newNoti = {
            id: Date.now(),
            type: data.type,
            message: data.type === 'SYNC_ERROR' 
              ? `Lỗi đồng bộ Site ${data.node?.toUpperCase()}`
              : `Đã khôi phục Site ${data.node?.toUpperCase()}`,
            description: data.message,
            time: new Date().toLocaleString()
          };

          setNotifications(prev => {
            const updated = [newNoti, ...prev].slice(0, 50); // Giữ tối đa 50 thông báo gần nhất
            localStorage.setItem('sync_notifications', JSON.stringify(updated));
            return updated;
          });

          // Hiển thị Toast
          if (data.type === 'SYNC_ERROR') {
            notification.error({
              message: newNoti.message,
              description: newNoti.description,
              duration: 5,
              placement: 'topRight'
            });
          } else if (data.type === 'SYNC_SUCCESS') {
            notification.success({
              message: newNoti.message,
              description: newNoti.description,
              duration: 5,
              placement: 'topRight'
            });
          }
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      };

      ws.onclose = () => {
        // Tự động kết nối lại sau 3 giây
        setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.onclose = null; // Ngăn chặn vòng lặp kết nối lại khi component unmount
        ws.close();
      }
    };
  }, []);

  const handleClearHistory = () => {
    setNotifications([]);
    localStorage.removeItem('sync_notifications');
  };

  return (
    <>
      {/* Nút Chuông Thông Báo */}
      <button 
        onClick={() => setIsOpen(true)}
        className={styles.bellBtn}
        aria-label="Lịch sử thông báo"
      >
        <Bell size={28} weight="bold" />
        {notifications.length > 0 && (
          <span className={styles.badge}>
            {notifications.length > 99 ? '99+' : notifications.length}
          </span>
        )}
      </button>

      {/* Drawer Overlay */}
      <div 
        className={`${styles.overlay} ${isOpen ? styles.overlayOpen : ''}`} 
        onClick={() => setIsOpen(false)}
      />

      {/* Custom Sliding Drawer Panel */}
      <div className={`${styles.drawer} ${isOpen ? styles.drawerOpen : ''}`}>
        <div className={styles.header}>
          <h3 className={styles.title}>Lịch sử đồng bộ hệ thống</h3>
          <button 
            className={styles.closeBtn} 
            onClick={() => setIsOpen(false)}
            type="button"
          >
            <X size={20} weight="bold" />
          </button>
        </div>

        <div className={styles.body}>
          {notifications.length === 0 ? (
            <div className={styles.emptyState}>
              <Bell size={48} weight="thin" style={{ opacity: 0.5 }} />
              <p className={styles.emptyText}>Chưa có thông báo nào được ghi nhận.</p>
            </div>
          ) : (
            <>
              <div className={styles.clearBtnContainer}>
                <button 
                  onClick={handleClearHistory}
                  className={styles.clearBtn}
                  type="button"
                >
                  Xóa lịch sử
                </button>
              </div>
              {notifications.map(n => (
                <div 
                  key={n.id} 
                  className={`${styles.card} ${
                    n.type === 'SYNC_ERROR' ? styles.cardError : styles.cardSuccess
                  }`}
                >
                  <div className={styles.cardHeader}>
                    <strong className={`${styles.cardTitle} ${
                      n.type === 'SYNC_ERROR' ? styles.cardTitleError : styles.cardTitleSuccess
                    }`}>
                      {n.message}
                    </strong>
                    <span className={styles.time}>{n.time}</span>
                  </div>
                  <div className={styles.description}>{n.description}</div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </>
  );
}
