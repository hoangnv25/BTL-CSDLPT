# Bảng Kết Quả So Sánh Hiệu Năng

| Chỉ số | Tập trung (Centralized) | Phân tán (Distributed) | Phân tán khi sập 1 Node (Failover) |
| :--- | :---: | :---: | :---: |
| **Tổng số Request** | 2862 | 2922 | 2576 |
| **Throughput (Tốc độ xử lý)** | 143.06 req/s | 145.40 req/s | 128.40 req/s |
| **Độ trễ trung bình (Avg Latency)** | 384.03 ms | 372.24 ms | 437.45 ms |
| **Độ trễ phân vị P90** | 824.87 ms | 823.97 ms | 756.00 ms |
| **Độ trễ phân vị P95** | 891.47 ms | 922.09 ms | 981.10 ms |
| **Tỷ lệ lỗi (Error %)** | 0.00% | 0.00% | 1.82% |
| **Trạng thái hoạt động** | Bình thường | Bình thường | Tự phục hồi (Auto-recovered) |
