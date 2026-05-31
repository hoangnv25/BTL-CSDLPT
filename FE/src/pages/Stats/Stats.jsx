import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Select, DatePicker, Typography, Spin, Space, Tag } from 'antd';
import { ShoppingBag, ChartLineUp, Storefront, TrendUp, Money } from '@phosphor-icons/react';
import dayjs from 'dayjs';
import styles from './Stats.module.css';

const { Title, Text } = Typography;
const { Option } = Select;

export default function Stats({ warehouse_id = null }) {
  const [loading, setLoading] = useState(false);
  const [topProducts, setTopProducts] = useState([]);
  const [revenueData, setRevenueData] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  
  // Filters
  const [period, setPeriod] = useState('month');
  const [warehouseId, setWarehouseId] = useState(warehouse_id);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

  // Cập nhật warehouseId khi prop thay đổi (ví dụ khi chuyển manager)
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
      
      if (selectedDate) {
        queryParams += `&specific_date=${selectedDate.format('YYYY-MM-DD')}`;
      } else if (selectedMonth) {
        queryParams += `&specific_month=${selectedMonth.month() + 1}&specific_year=${selectedMonth.year()}`;
      }

      // Fetch Top Products
      const topRes = await fetch(`${API_BASE_URL}/stats/top-products?${queryParams}`);
      const topData = await topRes.json();
      setTopProducts(topData);

      // Fetch Revenue
      const revRes = await fetch(`${API_BASE_URL}/stats/revenue?${queryParams}`);
      const revData = await revRes.json();
      setRevenueData(revData);

    } catch (err) {
      console.error("Error fetching stats:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const productColumns = [
    {
      title: 'Hạng',
      key: 'rank',
      render: (_, __, index) => <Tag color={index < 3 ? 'gold' : 'blue'}>{index + 1}</Tag>,
      width: 80,
    },
    {
      title: 'Sản phẩm',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: 'Đơn giá',
      dataIndex: 'price',
      key: 'price',
      render: (val) => formatCurrency(val),
    },
    {
      title: 'Đã bán',
      dataIndex: 'total_sold',
      key: 'total_sold',
      render: (val) => <b style={{ color: 'var(--primary-color)' }}>{val}</b>,
    },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Title level={2}>
          Thống Kê Kinh Doanh 
          {warehouseId && warehouses.length > 0 && ` - ${warehouses.find(w => w.id === warehouseId)?.name || ''}`}
        </Title>
        <Space wrap>
          {!warehouse_id && (
            <Select 
              placeholder="Kho hàng" 
              style={{ width: 200 }} 
              allowClear
              onChange={setWarehouseId}
              value={warehouseId}
            >
              <Option value={null}>-- Toàn hệ thống --</Option>
              {warehouses.map(w => <Option key={w.id} value={w.id}>{w.name}</Option>)}
            </Select>
          )}
          
          <Select 
            value={period} 
            style={{ width: 120 }} 
            onChange={(val) => {
              setPeriod(val);
              setSelectedDate(null);
              setSelectedMonth(null);
            }}
          >
            <Option value="day">Ngày</Option>
            <Option value="month">Tháng</Option>
            <Option value="year">Năm</Option>
          </Select>

          <DatePicker 
            picker={period === 'month' ? 'month' : (period === 'year' ? 'year' : 'date')}
            placeholder={`Chọn ${period}`}
            onChange={(val) => {
              if (period === 'month') setSelectedMonth(val);
              else setSelectedDate(val);
            }}
          />
        </Space>
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card className={styles.statCard}>
              <Statistic
                title="Tổng Doanh Thu"
                value={revenueData?.total_revenue || 0}
                formatter={(val) => formatCurrency(val)}
                prefix={<ChartLineUp size={24} color="#52c41a" weight="bold" />}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className={styles.statCard}>
              <Statistic
                title="Tổng Kiện Hàng"
                value={revenueData?.total_packages || 0}
                prefix={<ShoppingBag size={24} color="#1890ff" weight="bold" />}
              />
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className={styles.statCard}>
              <Statistic
                title="Khu Vực"
                value={warehouseId ? warehouses.find(w => w.id === warehouseId)?.region : "Toàn hệ thống"}
                prefix={<Storefront size={24} color="#722ed1" weight="bold" />}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
          <Col span={24}>
            <Card title="Top 10 Sản Phẩm Bán Chạy">
              <Table 
                dataSource={topProducts} 
                columns={productColumns} 
                pagination={false}
                rowKey="product_id"
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
}
