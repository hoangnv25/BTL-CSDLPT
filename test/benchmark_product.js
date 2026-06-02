import http from 'k6/http';
import { check, sleep } from 'k6';

// Cấu hình các giai đoạn tăng tải nhanh và chịu tải cao
export const options = {
  scenarios: {
    default: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5s', target: 30 },   // Ramping up nhanh: Lên 30 users trong 5s
        { duration: '5s', target: 90 },   // Tải trung bình: Lên 90 users trong 5s
        { duration: '5s', target: 150 },  // Đỉnh: Lên 150 users trong 5s
        { duration: '5s', target: 0 },    // Ramping down nhanh về 0 trong 5s
      ],
      gracefulRampDown: '2s',             // Chờ tối đa 2s cho các VU khi ramp down để hoàn thành iteration dở
      gracefulStop: '2s',                 // Chờ tối đa 2s trước khi dừng bài test hoàn toàn
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.10'],       // Tỷ lệ lỗi cho phép dưới 10%
  },
};

export default function () {
  // Nhận target url từ biến môi trường (mặc định là localhost nếu chạy trực tiếp)
  const url = __ENV.TARGET_URL || 'http://localhost:8000/product';
  
  // Nhận target node từ biến môi trường: k6 run -e TARGET_NODE=main/auto
  const targetNode = __ENV.TARGET_NODE || 'main';

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Target-Node': targetNode,
    },
  };

  const res = http.get(url, params);

  // Kiểm tra tính chính xác của phản hồi
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body is not empty': (r) => r.body.length > 0,
  });

  // Nghỉ 100ms giữa các request của mỗi VU để giả lập hành vi thực tế và tránh nghẽn cục bộ quá nhanh
  sleep(0.1);
}
