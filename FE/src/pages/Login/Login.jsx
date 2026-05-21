import React, { useState } from 'react';
import { User, SignIn, UserPlus, IdentificationCard } from '@phosphor-icons/react';
import styles from './Login.module.css';

export default function Login({ onLoginSuccess }) {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (!username.trim()) {
      setError('Vui lòng nhập Username.');
      setLoading(false);
      return;
    }

    if (!isLoginMode && !fullName.trim()) {
      setError('Vui lòng nhập Họ tên.');
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLoginMode ? '/user/login' : '/user/register';
      const bodyData = isLoginMode 
        ? { username: username.trim() }
        : { username: username.trim(), full_name: fullName.trim() };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bodyData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.[0]?.msg || data.detail || 'Đã có lỗi xảy ra');
      }

      if (isLoginMode) {
        // Handle successful login
        localStorage.setItem('currentUser', JSON.stringify(data));
        onLoginSuccess(data);
      } else {
        // Handle successful register
        setSuccess('Đăng ký thành công! Đang tự động đăng nhập...');
        // Auto login after register
        setTimeout(() => {
          localStorage.setItem('currentUser', JSON.stringify(data));
          onLoginSuccess(data);
        }, 1500);
      }
    } catch (err) {
      setError(err.message || 'Không thể kết nối đến máy chủ');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setError('');
    setSuccess('');
    setUsername('');
    setFullName('');
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>
            {isLoginMode ? 'Đăng Nhập' : 'Đăng Ký'}
          </h1>
          <p className={styles.subtitle}>
            {isLoginMode 
              ? 'Nhập username để truy cập hệ thống quản lý' 
              : 'Tạo tài khoản mới để bắt đầu sử dụng'}
          </p>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {success && <div className={styles.success}>{success}</div>}

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Username</label>
            <div className={styles.inputWrapper}>
              <User className={styles.icon} size={20} weight="fill" />
              <input
                type="text"
                className={styles.input}
                placeholder="Nhập tên đăng nhập..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading || success !== ''}
              />
            </div>
          </div>

          {!isLoginMode && (
            <div className={styles.inputGroup}>
              <label className={styles.label}>Họ và Tên</label>
              <div className={styles.inputWrapper}>
                <IdentificationCard className={styles.icon} size={20} weight="fill" />
                <input
                  type="text"
                  className={styles.input}
                  placeholder="Nhập họ và tên của bạn..."
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={loading || success !== ''}
                />
              </div>
            </div>
          )}

          <button 
            type="submit" 
            className={styles.button}
            disabled={loading || success !== ''}
          >
            {loading ? (
              'Đang xử lý...'
            ) : (
              <>
                {isLoginMode ? <SignIn size={20} weight="bold" /> : <UserPlus size={20} weight="bold" />}
                {isLoginMode ? 'Đăng Nhập' : 'Tạo Tài Khoản'}
              </>
            )}
          </button>
        </form>

        <div className={styles.toggleContainer}>
          {isLoginMode ? (
            <p>
              Chưa có tài khoản?{' '}
              <button type="button" onClick={toggleMode} className={styles.toggleLink}>
                Đăng ký ngay
              </button>
            </p>
          ) : (
            <p>
              Đã có tài khoản?{' '}
              <button type="button" onClick={toggleMode} className={styles.toggleLink}>
                Đăng nhập
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
