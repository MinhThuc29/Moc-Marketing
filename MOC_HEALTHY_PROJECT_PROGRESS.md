# MỘC HEALTHY — PROJECT PROGRESS
## Living Project Status for AI-assisted Development

> Đây là file trạng thái sống của dự án.  
> Mọi coding agent phải đọc file này **sau `docs/PLAN.md` và trước khi code**.
>
> Sau mỗi task/prompt, agent phải cập nhật file này để phiên làm việc tiếp theo biết:
> - Đã làm gì.
> - Đang làm gì.
> - Còn thiếu gì.
> - Có lỗi/blocker gì.
> - Migration/API nào đã thay đổi.
> - Prompt tiếp theo nên chạy là gì.
>
> **Không xóa lịch sử đã hoàn thành. Không tự đánh dấu DONE nếu test/build chưa pass.**

---

# 1. Project Snapshot

| Field | Value |
|---|---|
| Project | Mộc Healthy AI Marketing & Commerce Platform |
| Current Phase | Phase 4 — AI Content & AI Foundation (IN_PROGRESS) |
| Current Prompt | PROMPT 19 — AI Provider Abstraction |
| Overall Status | IN_PROGRESS |
| Overall Progress | 76% |
| Last Updated | 2026-10-08 15:20 |
| Updated By | Principal Architect / Senior Full-stack Engineer |
| Current Branch | main |
| Last Commit | - |
| Next Recommended Prompt | PROMPT 20 — AI Content Studio |

## Status Legend

```text
NOT_STARTED
IN_PROGRESS
BLOCKED
REVIEW
DONE
SKIPPED
```

---

# 2. Golden Rules for Progress Tracking

1. Chỉ đánh dấu `DONE` khi acceptance criteria của task đã đạt.
2. Nếu code xong nhưng test/build chưa pass → `REVIEW` hoặc `BLOCKED`, không phải `DONE`.
3. Nếu dependency ngoài hệ thống chưa có credential → ghi rõ `BLOCKED_EXTERNAL`, nhưng mock path vẫn phải hoạt động nếu PLAN yêu cầu.
4. Mọi migration phải ghi vào mục `Database Changes`.
5. Mọi API mới/thay đổi phải ghi vào `API Changes`.
6. Mọi quyết định kiến trúc đáng kể phải ghi vào `Decision Log`.
7. Không reset progress về 0 khi mở session mới.
8. Không xóa blocker cũ; chuyển sang `RESOLVED`.
9. Sau mỗi session phải cập nhật `Next Action`.
10. Nếu PLAN thay đổi, phải ghi rõ lý do và phần bị ảnh hưởng.

---

# 3. Phase Progress

## Phase 0 — Foundation

**Goal:** repository, infrastructure, auth foundation, design system, CI baseline.

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 01 | Bootstrap Repository | DONE | 100% | Monorepo layout, Next.js apps, FastAPI, worker, docker-compose, healthcheck |
| 02 | Authentication + RBAC | DONE | 100% | User/Role/Permission DB, JWT rotation, rate limiter, login/me, Admin login UI, ProtectedRoute, AdminNav |
| 03 | Admin Design System & App Shell | DONE | 100% | Brand design system, full reusable UI library, responsive AdminShell, 10 Information Architecture module pages |

**Phase 0 Status: COMPLETE (10/10 Exit Criteria Satisfied)**

---

## Phase 1 — Commerce Core

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 04 | Product & Category Backend | DONE | 100% | Category & Product models, migration 002, CRUD API, search, filter, sort, pagination, bulk status, price invariant validation, audit logging, 10 demo products seeded, 25 tests |
| 05 | Product Admin UI | DONE | 100% | Bảng sản phẩm, bộ lọc, tìm kiếm, Drawer thêm/sửa với guardrail giá, modal lịch sử kiểm toán giá, quản lý danh mục, bulk status, RBAC |
| 06 | Media Upload + Media Library | DONE | 100% | Storage abstraction (Local + MinIO), Pillow WebP thumbnail, bảng media_assets, migration 003, upload endpoint, MediaLibraryModal, tích hợp chọn ảnh trong ProductFormDrawer |
| 07 | Inventory & Expiry | DONE | 100% | Batch-based inventory, FEFO allocation algorithm, migration 004, movements ledger, negative stock protection, expiry alerts, Admin UI (/inventory) 4 tabs & 3 modals, 8 tests |
| 08 | Promotion Engine | DONE | 100% | Authoritative backend engine (7 types: % discount, fixed, flash sale, buy X get Y, combo, freeship, voucher), deterministic math, max cap, scope filter, dry-run calculate API, Admin UI (/promotions) with Drawer & Simulator Modal, 8 tests |
| 09 | Storefront Foundation | DONE | 100% | Mobile-first storefront web (Home, Category, Product detail, Search, Promotion, 404), public Storefront API, SEO metadata, responsive cards, 7 tests |
| 10 | Cart + Checkout | DONE | 100% | Guest & authenticated cart, DB persistence, migration 006, authoritative price recalculation, voucher evaluation, COD & VietQR transfer, tracking hooks, 10 tests |
| 11 | Order Management | DONE | 100% | Vòng đời đơn hàng khép kín (NEW -> CONFIRMED -> PREPARING -> READY -> SHIPPING -> COMPLETED/CANCELLED/REFUNDED), máy trạng thái guardrail, hoàn tồn kho tự động khi hủy (RETURN_IN), timeline kiểm toán, Admin Order Drawer & Modal tạo đơn tại quầy, Trang tra cứu đơn hàng công khai (/tracking), 8 tests |
| 11A | Omnichannel Order Hub + Marketplace Import | DONE | 100% | Ingestion báo cáo bán hàng GrabFood & ShopeeFood CSV/XLSX, tính toán và phân tách Gross Sales vs Platform Fee (20-25%) vs Merchant Promo vs Net Settlement, Settlement & Auto-Reconciliation đối soát sao kê sàn, Channel P&L Analytics, Admin UI Modals & PnL View, 6 tests (95 total) |

**Phase 1 Status: COMPLETE (9/9 Core Tasks Complete — 100%)**

---

## Phase 2 — Customer CRM & Marketing Engine

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 12 | Customer CRM & Loyalty Hub | DONE | 100% | Hồ sơ Customer 360, định danh số điện thoại, phân nhóm tự động RFM (NEW, ACTIVE, REPEAT, VIP, AT_RISK, DORMANT, HIGH_VALUE), tích lũy điểm Mộc Xu (1 điểm / 10k VND), sổ cái Loyalty, Admin UI (/customers) với Drawer 360 & Modal điều chỉnh điểm, 6 tests (101 total) |
| 13 | Campaign Management & Multi-channel Hub | DONE | 100% | Quản lý chiến dịch tiếp thị đa kênh (Facebook, Zalo, TikTok, Instagram, SMS, Email, Web Banner), máy trạng thái phê duyệt (DRAFT -> READY_FOR_REVIEW -> APPROVED -> ACTIVE -> COMPLETED), tính toán ngân sách vs doanh thu & ROI %, hero products, Admin UI (/marketing) StatCards, Status Tabs, Drawer, Modal, 5 tests (106 total) |
| 14 | AI Content Studio & Social Media Auto-publish | DONE | 100% | Kịch bản nội dung đa kênh, AI F&B copywriter (AIDA & PAS models), storyboard video TikTok 45s, Zalo OA broadcast, quy trình duyệt Human-in-the-loop, social mock publisher adapter, Admin UI (/content Hub & Calendar & /ai-studio Wizard), 6 tests (112 total) |
| 15 | Marketing Analytics & Attribution Engine | DONE | 100% | Multi-touch attribution (First, Last, Linear, Time-decay), Ingestion clickstream (/events, /batch), AttributionService, AnalyticsService (Gross/Net P&L, ROAS, MER, CAC, LTV), Admin UI (/analytics) 6 Executive KPI Cards, 4 Tabs (Omnichannel P&L, Attribution Engine, Conversion Funnel, AI Insights), 6 tests (118 total) |

**Phase 2 Status: COMPLETE (4/4 Tasks Complete — 100%)**

---

## Phase 3 — Marketing Automation & Intelligence Foundation

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 16 | Marketing Automation & Customer Journeys | DONE | 100% | Workflow Engine (5 MVP triggers: WELCOME, ABANDONED_CART, REPEAT_PURCHASE, REACTIVATION_AT_RISK, INVENTORY_CLEARANCE), Flexible Condition Evaluator, Multi-action Executor, Dispatcher & Dry-Run Simulator, Alembic migration 012, Admin UI (/automation) with StatCards, Tabs, Drawer, Modals, 6 tests (124 total) |
| 17 | AI Recommendation Engine & Smart Alerts | DONE | 100% | Evidence-based recommendation engine (Clearance, Campaign, Retention, Channel), 1-Click Convert to Campaign / Workflow, Smart Alerts Engine (CRITICAL/WARNING/INFO), Alembic 013, Admin UI Dual Tabs (/ai-studio) + Topbar alerts bell, 7 tests (131 total) |

**Phase 3 Status: COMPLETE (2/2 Tasks Complete — 100%)**

---

## Phase 4 — AI Content & AI Foundation

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 19 | AI Provider Abstraction | DONE | 100% | BaseAIProvider interface, MockAIProvider, GeminiProvider, OpenAIProvider, registry, PII masking guardrail (phone/email/id), Prompt templates versioning, AIGenerationLog audit & token metrics, Alembic 015, Admin UI (/settings tab AI), 9 tests (148 total) |
| 20 | AI Content Studio | NOT_STARTED | 0% | Bộ sinh Content Pack hoàn chỉnh theo sản phẩm, chiến dịch, brand tone, channels & định dạng đa phương tiện |

---

## Phase 5 — Real Social Publishing & Provider Adapters

| Prompt | Work Item | Status | Progress | Notes |
|---|---|---:|---:|---|
| 18 | Social Publishing Engine & Multi-Platform Provider Adapters | DONE | 100% | SocialProvider interface, MockSocialProvider (Facebook, Instagram, TikTok, Zalo OA), WebsitePublisher (Storefront Blog), SocialPublishingService (AsyncSession, Idempotency Guard, Exponential Backoff, Background Batch Worker, Post Metrics Sync), Alembic migration 014, Admin UI (/content tab social, /settings tab social, ContentDetailDrawer publish-now button), 8 tests (139 total) |

**Phase 5 Status: COMPLETE (1/1 Task Complete — 100%)**

---

# 4. Current Task

## Task

```text
Prompt: PROMPT 19 — AI Provider Abstraction
Status: DONE
Started: 2026-10-08 14:55
Finished: 2026-10-08 15:20
Owner: Principal Software Architect / Senior Full-stack Engineer
Branch: main
```

## Scope

- **Database Models & Alembic Migration 015**:
  - `PromptTemplate`: `id`, `slug`, `name`, `category`, `version` (int), `system_prompt`, `user_prompt_template`, `input_variables` (JSON list), `expected_output_schema`, `is_active`, `created_at`, `updated_at`.
  - `AIGenerationLog`: `id`, `provider_name`, `model_name`, `prompt_template_id`, `prompt_slug`, `prompt_version`, `input_prompt_sanitized`, `system_prompt_sanitized`, `raw_output`, `parsed_json`, `status` (`SUCCESS`, `FAILED`, `TIMEOUT`, `VALIDATION_ERROR`), `error_message`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `estimated_cost_usd`, `latency_ms`, `retry_count`, `created_by_user_id`, `created_at`.
  - Migration Alembic: `015_create_ai_provider_tables.py` tạo 2 bảng với composite indexes trên SQLite test và production DB.
- **Provider Abstraction Architecture (`app/services/ai_providers`)**:
  - `BaseAIProvider`: Abstract class (`generate_text`, `generate_json`, `analyze`, `health_check`).
  - `MockAIProvider`: Dùng cho testing và offline development, hỗ trợ cờ mô phỏng (`simulate_timeout`, `simulate_malformed_json`, `simulate_transient_failure`, `is_available`), tính toán token & chi phí USD giả lập.
  - `GeminiProvider`: Adapter tương thích Google Gemini API v1beta REST qua `httpx`, hỗ trợ JSON schema output mode và usage metadata.
  - `OpenAIProvider`: Adapter tương thích OpenAI Chat Completions REST API qua `httpx`.
  - Registry Factory: `get_ai_provider()` tự động nạp provider từ biến môi trường `AI_PROVIDER` (mặc định `'mock'`).
- **PII Sanitizer Guardrail (`mask_pii`)**:
  - Tự động phát hiện và che giấu triệt để thông tin cá nhân khách hàng (số điện thoại Việt Nam `[SĐT_ĐÃ_ẨN]`, email `[EMAIL_ĐÃ_ẨN]`, CCCD/CMND `[ID_ĐÃ_ẨN]`) trước khi gửi đến bất kỳ AI Provider nào bên ngoài.
- **AI Service (`AIService`)**:
  - Điều phối quy trình sinh nội dung: PII Sanitization -> Render Prompt Template -> Gọi Provider với Timeout & Exponential Backoff Retry -> Pydantic Schema Validation -> Ghi nhận toàn diện vào `AIGenerationLog`.
  - Quản lý kho PromptTemplate (CRUD và tăng version `version += 1`).
  - Truy vấn Audit Logs và Telemetry chi phí.
- **Demo Seed Data**:
  - `seed_demo_ai_templates`: Nạp 5 prompt templates F&B thực tế (Facebook AIDA, TikTok 45s script, xả kho tồn cận date, phản hồi CSKH, ý tưởng chiến dịch xanh) và 3 nhật ký telemetry mẫu.
- **REST API Routers (`/api/v1/ai`)**:
  - `GET /api/v1/ai/health`: Kiểm tra sức khỏe provider (ONLINE/OFFLINE, latency, model).
  - `GET /api/v1/ai/providers`: Danh sách nhà cung cấp được hỗ trợ.
  - `GET /api/v1/ai/templates`: Danh sách prompt templates.
  - `GET /api/v1/ai/templates/{slug}`: Chi tiết prompt template.
  - `POST /api/v1/ai/templates`: Tạo prompt template mới (RBAC).
  - `PUT /api/v1/ai/templates/{id}`: Cập nhật prompt template (bump version).
  - `POST /api/v1/ai/test-generate`: Thử nghiệm AI Sandbox (PII masking, structured JSON validation, token tracking).
  - `GET /api/v1/ai/logs`: Xem lịch sử generation logs.
  - `GET /api/v1/ai/logs/{id}`: Chi tiết một generation log.
- **Frontend Admin UI (`AIProviderManager`)**:
  - Tích hợp vào Tab `🤖 Cấu hình AI Provider` tại `/settings`.
  - 4 Phân hệ trực quan:
    1. Active Provider Health Card (Status ONLINE, Latency ms, Nút Ping Health).
    2. Kho Prompt Templates (Xem nội dung, phiên bản, biến đầu vào).
    3. AI Test Sandbox Playground (Test tự do / theo template, ép kiểu JSON, kiểm thử sự cố Resilience, hộp hiển thị Prompt đã qua lọc PII).
    4. Bảng Audit Logs & Token Telemetry (Theo dõi tokens, chi phí USD, thời gian thực thi).
- **Tests & Production Build**:
  - 9 integration test cases trong `apps/api/tests/test_ai_provider.py` (Health, Providers, Structured JSON, Malformed JSON, Timeout, Retry, Unavailable, PII Guardrail, Versioning & RBAC) — **9/9 PASSED (100%)**.
  - **148/148 backend tests passed (100%)**.
  - **Typecheck 0 errors** trên toàn bộ 4 workspace monorepo.
  - **Production build Next.js 100% thành công** (admin-web 17 static pages, storefront-web 10 pages).

## Acceptance Criteria

- [x] Giao diện trừu tượng `AIProvider` độc lập với mô hình cụ thể.
- [x] Hỗ trợ cấu hình provider qua biến môi trường (`AI_PROVIDER`, `AI_TIMEOUT_SECONDS`, `AI_MAX_RETRIES`).
- [x] Quản lý lưu trữ phiên bản Prompt Template (`version`).
- [x] Ghi nhận số lượng tokens, chi phí USD, độ trễ và nhật ký lỗi vào `AIGenerationLog`.
- [x] Cơ chế Timeout và Exponential Backoff Retry khi gặp lỗi tạm thời.
- [x] Kiểm tra tính hợp lệ dữ liệu JSON có cấu trúc bằng Pydantic.
- [x] Guardrail khử PII ngăn chặn rò rỉ số điện thoại và email khách hàng.
- [x] Triển khai `MockAIProvider` phục vụ kiểm thử resilience và phát triển offline.
- [x] 100% không có lỗi TypeScript (0 errors), lint PASS, build PASS, 148/148 tests PASS.

## Files Changed

```text
- apps/api/app/models/ai.py
- apps/api/app/models/__init__.py
- apps/api/alembic/versions/015_create_ai_provider_tables.py
- apps/api/app/schemas/ai.py
- apps/api/app/schemas/__init__.py
- apps/api/app/services/ai_providers/base.py
- apps/api/app/services/ai_providers/sanitizer.py
- apps/api/app/services/ai_providers/mock_provider.py
- apps/api/app/services/ai_providers/gemini_provider.py
- apps/api/app/services/ai_providers/openai_provider.py
- apps/api/app/services/ai_providers/registry.py
- apps/api/app/services/ai_providers/__init__.py
- apps/api/app/services/ai_service.py
- apps/api/app/api/deps.py
- apps/api/app/api/v1/ai.py
- apps/api/app/api/v1/router.py
- apps/api/app/core/seed.py
- apps/api/app/main.py
- apps/api/tests/conftest.py
- apps/api/tests/test_ai_provider.py
- packages/contracts/src/index.ts
- apps/admin-web/src/lib/api.ts
- apps/admin-web/src/components/ai/AIProviderManager.tsx
- apps/admin-web/src/app/settings/page.tsx
- docs/PROJECT_PROGRESS.md
- MOC_HEALTHY_PROJECT_PROGRESS.md
```

## Commands Run

```bash
.\.venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m pytest apps/api/tests/test_ai_provider.py -v
.\.venv\Scripts\python.exe -m pytest apps/api/tests/ -v
npm.cmd run typecheck
npm.cmd run build
```

## Test Result

| Check | Status | Notes |
|---|---|---|
| Lint | PASS | Tất cả npm workspaces passed |
| Typecheck | PASS | Toàn bộ 4 TypeScript workspaces passed (0 errors) |
| Unit & Integration tests | PASS | Pytest: 148 passed, 0 failed (9 tests AI provider mới, 148/148 tổng cộng) |
| Build | PASS | Next.js admin-web (17 static pages) và storefront-web (10 pages) biên dịch production thành công |

---

# 5. Completed Work Log

### 2026-10-08 — PROMPT 19 — AI Provider Abstraction

**Status:** DONE

**Implemented**
- Kiến trúc Interface `BaseAIProvider` và các Adapter: `MockAIProvider`, `GeminiProvider`, `OpenAIProvider`.
- Mô hình cơ sở dữ liệu `PromptTemplate` (versioning) và `AIGenerationLog` (token, cost, latency audit) cùng migration Alembic `015_create_ai_provider_tables.py`.
- PII Sanitization Guardrail khử số điện thoại và email khách hàng trước khi gửi tới LLM.
- Cơ chế Timeout và Exponential Backoff Retry tự động khi gặp lỗi tạm thời.
- Pydantic structured output validation đảm bảo dữ liệu JSON đầu ra chính xác, không hallucination.
- 5 Prompt Templates F&B Mộc Healthy và 3 nhật ký telemetry mẫu nạp sẵn.
- REST API Router `/api/v1/ai` với 9 endpoints hoàn chỉnh.
- Component Admin `AIProviderManager` tại trang Cài đặt Hệ thống (`/settings` tab AI).
- 9 tests integration backend bao quát toàn diện các yêu cầu kỹ thuật (148/148 tests passed 100%).

### 2026-10-08 — PROMPT 18 — Social Publishing Engine & Multi-Platform Provider Adapters

**Status:** DONE

**Implemented**
- Kiến trúc Provider Adapter trừu tượng hóa mạng xã hội `SocialProvider`, `MockSocialProvider` và `WebsitePublisher`.
- Mô hình dữ liệu `SocialConnection`, `PublishedPost`, `PostMetric` và migration Alembic `014_create_social_publishing_tables.py`.
- `SocialPublishingService`: Xuất bản đa kênh tức thì, bảo vệ idempotency không xuất bản trùng lặp, cơ chế worker batch pickup cho bài `SCHEDULED` và bài lỗi `FAILED` với exponential backoff.
- 5 Kết nối mạng xã hội mẫu và 3 bài viết có chỉ số tương tác nạp sẵn trong hệ thống.
- Router RESTful `/api/v1/social` với 11 endpoints hoàn chỉnh.
- Component `SocialPublishingManager` tích hợp tại Content Hub (`/content`), Settings (`/settings`) và nút Xuất bản ngay tại `ContentDetailDrawer`.
- 8 tests integration backend bao quát toàn diện quy trình xuất bản, bảo vệ idempotency, batch worker, sync metrics và RBAC (139/139 tests passed 100%).

---

# 9. Database Changes

| Date | Migration | Tables Added / Changed | Destructive | Target DB | Tested | Purpose |
|---|---|---|---|---|---|---|
| 2026-10-08 | 015_ai_provider | `prompt_templates`, `ai_generation_logs` | No | SQLite test / Ready Postgres | Yes | Quản lý mẫu Prompt chuẩn hóa với kiểm soát phiên bản (versioning) và nhật ký thực thi AI ghi nhận token, chi phí, độ trễ và dấu vết khử PII |
| 2026-10-08 | 014_social_publishing | `social_connections`, `published_posts`, `post_metrics` | No | SQLite test / Ready Postgres | Yes | Quản lý kết nối mạng xã hội đa kênh OAuth, hàng đợi xuất bản bài viết, idempotency, retry backoff và chuỗi thời gian chỉ số tương tác |
| 2026-10-08 | 013_recommendations_and_alerts | `ai_recommendations`, `smart_alerts` | No | SQLite test / Ready Postgres | Yes | Quản lý khuyến nghị chiến lược tiếp thị dựa trên chứng cứ thực tế DB, 1-Click Convert và cảnh báo rủi pro vận hành thời gian thực |
| 2026-10-08 | 012_marketing_automation | `automation_workflows`, `automation_runs` | No | SQLite test / Ready Postgres | Yes | Quản lý kịch bản tự động hóa tiếp thị, hành trình khách hàng (triggers, conditions, actions) và nhật ký thực thi |
| 2026-10-08 | 011_analytics_and_attribution | `tracking_events`, `conversion_attributions` | No | SQLite test / Ready Postgres | Yes | Quản lý clickstream tracking events, phân bổ doanh thu đa mô hình (First/Last/Linear/Time-decay) và độ tin cậy |
| 2026-10-08 | 010_content_studio | `content_items` | No | SQLite test / Ready Postgres | Yes | Quản lý nội dung bài viết tiếp thị, kịch bản video, hook, metrics và trạng thái xuất bản mạng xã hội |
| 2026-10-08 | 009_campaigns | `campaigns`, `campaign_channels`, `campaign_products` | No | SQLite test / Ready Postgres | Yes | Quản lý chiến dịch tiếp thị đa kênh, ngân sách, hero products và mục tiêu chuyển đổi |
| 2026-10-07 | 008_customer_crm | `customers`, `customer_addresses`, `loyalty_transactions`, thêm cột `customer_id` vào `orders` | No | SQLite test / Ready Postgres | Yes | Quản lý hồ sơ khách hàng hợp nhất, danh bạ địa chỉ, sổ cái điểm thưởng Mộc Xu và phân nhóm RFM |
| 2026-10-07 | 007_omnichannel_settlement | `marketplace_imports`, `settlements`, `settlement_orders`, thêm cột tài chính vào `orders` | No | SQLite test / Ready Postgres | Yes | Quản lý nhập đơn hàng sàn GrabFood/ShopeeFood, sao kê đối soát và phân tách Gross vs Net |
| 2026-10-07 | 006_cart_orders | `carts`, `cart_items`, `orders`, `order_items`, `order_status_history` | No | SQLite test / Ready Postgres | Yes | Quản lý giỏ hàng khách hàng, đơn hàng, snapshot chi tiết món và lịch sử trạng thái đơn hàng |
| 2026-10-07 | 005_promotions | `promotions`, `promotion_usages` | No | SQLite test / Ready Postgres | Yes | Quản lý 7 loại hình khuyến mãi, mã voucher và lịch sử áp dụng khuyến mãi |
| 2026-10-07 | 004_inventory | `inventory_batches`, `inventory_movements`, thêm cột `low_stock_threshold` vào `products` | No | SQLite test / Ready Postgres | Yes | Quản lý tồn kho theo lô F&B, lịch sử luân chuyển sổ cái và định mức tồn kho tối thiểu |
| 2026-10-07 | 003_media_assets | `media_assets` | No | SQLite test / Ready Postgres | Yes | Bảng lưu trữ metadata hình ảnh/video đa phương tiện và thumbnail |
| 2026-10-07 | 002_product_category | `categories`, `products`, `price_audit_logs` | No | SQLite test / Ready Postgres | Yes | Bảng danh mục, sản phẩm F&B và nhật ký kiểm toán biến động giá |
| 2026-10-07 | 001_auth_rbac | `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `refresh_tokens` | No | SQLite test / Ready Postgres | Yes | Tạo cấu trúc bảng xác thực và phân quyền RBAC |

---

# 10. API Changes

| Date | Method | Endpoint | Change | Backward Compatible | Notes |
|---|---|---|---|---|---|
| 2026-10-08 | GET | `/api/v1/ai/health` | Kiểm tra sức khỏe provider đang kích hoạt | Yes | Trả về status, model, latency, is_mock |
| 2026-10-08 | GET | `/api/v1/ai/providers` | Danh sách các AI provider được hỗ trợ | Yes | MOCK, GEMINI, OPENAI |
| 2026-10-08 | GET | `/api/v1/ai/templates` | Danh sách Prompt Templates | Yes | Lọc theo category, is_active |
| 2026-10-08 | GET | `/api/v1/ai/templates/{slug}` | Chi tiết Prompt Template | Yes | Lấy theo slug duy nhất |
| 2026-10-08 | POST | `/api/v1/ai/templates` | Tạo Prompt Template mới | Yes | Tự động gán version = 1 |
| 2026-10-08 | PUT | `/api/v1/ai/templates/{id}` | Cập nhật Prompt Template | Yes | Hỗ trợ bump_version tăng version |
| 2026-10-08 | POST | `/api/v1/ai/test-generate` | Thử nghiệm AI Sandbox | Yes | PII masking, structured JSON, tokens |
| 2026-10-08 | GET | `/api/v1/ai/logs` | Danh sách nhật ký gọi AI | Yes | Lọc provider, status, limit, offset |
| 2026-10-08 | GET | `/api/v1/ai/logs/{id}` | Chi tiết một bản ghi generation log | Yes | Xem prompt_sanitized, tokens, cost |
| 2026-10-08 | GET | `/api/v1/social/connections` | Danh sách kết nối mạng xã hội | Yes | Lọc theo platform, status, is_connected |
| 2026-10-08 | POST | `/api/v1/social/connections` | Thêm mới kết nối mạng xã hội | Yes | Hỗ trợ Sandbox mock hoặc Live API |

---

# 13. Test Health

| Suite | Total | Passed | Failed | Skipped | Last Run |
|---|---:|---:|---:|---|---|
| Backend Unit & Integration | 148 | 148 | 0 | 0 | 2026-10-08 15:15 |
| Frontend Typecheck | 4 | 4 | 0 | 0 | 2026-10-08 15:07 |
| Frontend Build | 2 | 2 | 0 | 0 | 2026-10-08 15:18 |
| E2E | 0 | 0 | 0 | 0 | - |

---

# 14. Release Readiness

## Phase 0 Readiness: COMPLETE (10/10)

## Phase 1 Progress: 9/9 Tasks Complete (100% Phase 1 Done)

## Phase 2 Progress: 4/4 Tasks Complete (100% Phase 2 Done — COMPLETE)

## Phase 3 Progress: 2/2 Tasks Complete (100% Phase 3 Done — COMPLETE)

## Phase 4 Progress: 1/2 Tasks Complete (50% Phase 4 Done — IN_PROGRESS)
- [x] PROMPT 19 — AI Provider Abstraction.
- [ ] PROMPT 20 — AI Content Studio.

## Phase 5 Progress: 1/1 Task Complete (100% Phase 5 Done — COMPLETE)
- [x] PROMPT 18 — Social Publishing Engine & Multi-Platform Provider Adapters.

---

# 15. Next Action

## Next Prompt

```text
PROMPT 20 — AI Content Studio
```

## Why This Is Next

Theo tài liệu thiết kế `MOC_HEALTHY_VIBE_CODING_PROMPTS.md` và `docs/PLAN.md` (Phase 4: AI Content):
1. **Đầu vào hoàn chỉnh (Input Context)**:
   - `product` (Món ăn / Nước ép), `campaign` (Chiến dịch), `audience` (Khách hàng mục tiêu), `promotion` (Khuyến mãi), `brand_tone` (Giọng điệu), `channels` (Facebook, TikTok, Zalo, Instagram), `desired_formats` (Bài viết, Storyboard, Zalo message).
2. **Sinh bộ nội dung toàn diện (Content Pack)**:
   - Sản sinh đồng thời nhiều biến thể bài viết theo kênh và mục tiêu tiếp thị.
   - Sử dụng các Prompt Templates đã xây dựng ở PROMPT 19 (`fb-copywriting-aida`, `tiktok-short-video-script`, v.v.).
   - Khử PII tự động, ghi nhận số lượng tokens và chi phí thực thi.
3. **Chuyển tiếp Human-in-the-loop**:
   - Cho phép duyệt, chỉnh sửa và đẩy vào hàng đợi xuất bản tự động (`SocialPublishingService` từ PROMPT 18).
