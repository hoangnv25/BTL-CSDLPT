# FastAPI + MySQL + Docker (Auto Reload)

## Chạy dự án

```bash
docker compose up --build
```

Sau khi chạy:

- **Frontend (React + Vite):** <http://localhost:5173>
- **Backend API Docs:** <http://localhost:8000/docs>
- **MySQL chính (từ máy host):** `localhost:3307` (user: `user` / pass: `123`, root pass: `root`)
- **MySQL Nodes (cho CSDL Phân Tán - để trống phục vụ thiết lập sau):**
  - **Node 1:** `localhost:3308` (user: `user` / pass: `123`, root pass: `root`)
  - **Node 2:** `localhost:3309` (user: `user` / pass: `123`, root pass: `root`)
  - **Node 3:** `localhost:3310` (user: `user` / pass: `123`, root pass: `root`)

## Auto reload (Hot Reload)

Cả hai service `be` và `fe` đều mount source code từ máy host vào container để hỗ trợ tự động reload khi bạn sửa code:

- **Backend (`be`):** Mount `./:/app` và chạy Uvicorn với `--reload`. Khi sửa code Python, server sẽ tự động tải lại.
- **Frontend (`fe`):** Mount `./FE:/app` và chạy Vite dev server. Khi bạn chỉnh sửa bất kỳ file nào trong folder `FE/`, giao diện sẽ tự động cập nhật ngay lập tức (Hot Module Replacement).


