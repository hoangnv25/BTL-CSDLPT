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