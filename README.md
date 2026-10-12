# Mộc Healthy — AI Marketing & Omnichannel Commerce Platform

Nền tảng thương mại F&B và Marketing tự động hóa hướng dữ liệu cho thương hiệu **Mộc Healthy** (Trái cây cắt sẵn, nước ép nguyên chất, sinh tố & đồ uống healthy).

---

## 1. Cấu trúc Modular Monorepo

```text
moc-healthy/
├── apps/
│   ├── admin-web/             # Next.js 15 + TypeScript (Internal Operations & AI Hub)
│   ├── storefront-web/        # Next.js 15 + TypeScript (Consumer Commerce Portal)
│   └── api/                   # FastAPI + Python 3.12 (Core Commerce & Marketing API)
├── workers/
│   └── marketing-worker/      # Background Worker (Scheduler, AI & Attribution Tasks)
├── packages/
│   ├── contracts/             # Shared TypeScript schemas, enums, API envelopes
│   └── ui/                    # Reusable React UI design system (Button, Badge, Card...)
├── infra/
│   ├── docker/
│   │   └── nginx/             # Nginx reverse proxy routing
│   └── scripts/               # One-command development launch scripts (dev.ps1, dev.sh)
├── docs/
│   ├── PLAN.md                # Single source of truth (Master Technical & Product Plan)
│   └── PROJECT_PROGRESS.md    # Living progress tracking & audit log
├── docker-compose.yml         # Full local development container orchestration
├── .env.example               # Environment variables template
└── README.md
```

---

## 2. Bảng ánh xạ Ports & Dịch vụ

| Dịch vụ | Địa chỉ Local | Mô tả |
|---|---|---|
| **Storefront Web** | `http://localhost:3001` | Giao diện mua hàng trực tiếp cho khách hàng |
| **Admin Web** | `http://localhost:3000` | Cổng quản trị vận hành đa vai trò (CEO, Marketing, Sales, Kho) |
| **Backend API** | `http://localhost:8000` | FastAPI Core Backend Service |
| **API Docs (Swagger)** | `http://localhost:8000/docs` | Tài liệu OpenAPI tương tác |
| **API Health Check** | `http://localhost:8000/health` | Kiểm tra trạng thái hệ thống và các dịch vụ kết nối |
| **MinIO Console** | `http://localhost:9001` | Quản trị Object Storage (Media Assets) |
| **PostgreSQL** | `localhost:5432` | Cơ sở dữ liệu chính (DB: `moc_healthy`) |
| **Redis** | `localhost:6379` | In-memory cache & job queue |
| **Nginx Proxy** | `http://localhost:80` | Reverse proxy định tuyến toàn bộ stack |

---

## 3. Hướng dẫn khởi chạy Local

### Cách 1: One-command với Docker Compose (Khuyên dùng khi có Docker)

```bash
# Khởi chạy toàn bộ stack (Postgres, Redis, MinIO, API, Worker, Admin, Storefront, Nginx)
docker compose up --build
```

### Cách 2: Chạy trực tiếp (Local Native Development)

#### Bước 1: Chuẩn bị biến môi trường
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

#### Bước 2: Cài đặt Node packages & build shared packages
```bash
# Cài đặt toàn bộ workspaces
npm install

# Kiểm tra typecheck
npm run typecheck
```

#### Bước 3: Khởi chạy Python API
```bash
# Tạo và kích hoạt virtual environment
python -m venv .venv

# Kích hoạt venv:
# Windows: .venv\Scripts\Activate.ps1 (hoặc .venv\Scripts\activate.bat)
# Linux/macOS: source .venv/bin/activate

# Cài đặt dependencies
pip install -r apps/api/requirements.txt

# Khởi chạy FastAPI
uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

#### Bước 4: Khởi chạy Frontend apps
```bash
# Terminal 1: Khởi chạy Admin (port 3000)
npm run dev:admin

# Terminal 2: Khởi chạy Storefront (port 3001)
npm run dev:storefront
```

---

## 4. Kiểm tra chất lượng (Verification Commands)

```bash
# 1. Typecheck toàn bộ TypeScript workspaces
npm run typecheck

# 2. Lint toàn bộ workspaces
npm run lint

# 3. Build Next.js applications
npm run build

# 4. Chạy unit tests cho API
pytest apps/api/tests
```

---

## 5. Tiến độ & Kế hoạch tiếp theo
- Hiện tại: **Phase 0 — Foundation / PROMPT 01 — Bootstrap Repository (DONE)**.
- Tiếp theo: **PROMPT 02 — Authentication + RBAC** (User, Role, Permission tables, JWT access/refresh token, Alembic migration, login/logout endpoints, admin login UI).
- Chi tiết xem tại [`docs/PROJECT_PROGRESS.md`](docs/PROJECT_PROGRESS.md).
