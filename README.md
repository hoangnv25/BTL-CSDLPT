# FastAPI + MySQL + Docker (Auto Reload)

## Chạy dự án

```bash
docker compose up --build
```

Sau khi chạy:

- API docs: <http://localhost:8000/docs>
- Health DB: <http://localhost:8000/health/db>
- MySQL từ máy host (Workbench, CLI): `localhost:3307` (user/pass trong `.env`; root: `root` / `rootpassword`)

## Auto reload

Service `api` mount source code từ máy host vào container:

- `volumes: - ./:/app`
- Uvicorn chạy với `--reload`

Mỗi khi bạn sửa code Python, FastAPI sẽ tự reload.

