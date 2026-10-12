# MỘC HEALTHY — VIBE CODING PROMPTS
## Prompt-by-Prompt Implementation Playbook

> File này chứa các prompt theo đúng thứ tự để đưa cho coding agent cho đến khi hệ thống hoàn thành.  
> Không nên paste tất cả cùng lúc. Chạy từng prompt, review kết quả, commit, sau đó mới chuyển prompt tiếp theo.

---


---

# BẮT BUỘC — Project Progress Protocol

Ngoài `docs/PLAN.md`, dự án phải duy trì file:

```text
docs/PROJECT_PROGRESS.md
```

Đây là **living state** của dự án.

Mỗi coding agent phải thực hiện theo thứ tự:

```text
1. Read docs/PLAN.md
2. Read docs/PROJECT_PROGRESS.md
3. Inspect actual repository
4. Reconcile progress file với code thực tế
5. Thực hiện prompt hiện tại
6. Chạy test/build
7. Update docs/PROJECT_PROGRESS.md
8. Chỉ sau đó mới kết thúc session
```

Sau mỗi prompt, bắt buộc cập nhật:

- Current Phase.
- Current Prompt.
- Prompt status.
- Overall progress.
- Acceptance criteria.
- Files changed.
- Commands run.
- Test/build result.
- Blockers.
- Technical debt.
- Architecture decisions.
- Database migrations.
- API changes.
- Integration status.
- Next prompt.

Nếu `PROJECT_PROGRESS.md` nói một feature đã DONE nhưng code/test cho thấy chưa hoàn thành, **code thực tế là nguồn sự thật** và agent phải sửa lại trạng thái trong progress file.

Không được:
- tự đánh dấu DONE khi test fail;
- xóa lịch sử task;
- reset progress giữa các session;
- bỏ qua blocker;
- chuyển prompt mới khi prompt hiện tại chưa đạt acceptance criteria, trừ khi blocker được ghi rõ.


# Cách sử dụng

Mỗi session mới, mở đầu bằng **PROMPT 00**.

Sau đó thực hiện lần lượt:

```text
00 → 01 → 02 → ... → 30
```

Quy tắc:
- Một prompt = một nhóm thay đổi có thể review.
- Không yêu cầu agent build toàn bộ hệ thống trong một lượt.
- Sau mỗi prompt phải chạy test/build.
- Nếu agent phát hiện kiến trúc hiện tại khác PLAN, agent phải nêu impact trước khi thay đổi.
- Mọi provider ngoài hệ thống phải có mock adapter để development không bị block.

---

# PROMPT 00 — Global Operating Prompt

```text
Bạn là Principal Software Architect + Senior Full-stack Engineer + Senior Product Engineer.

Dự án: Mộc Healthy AI Marketing & Commerce Platform.

Trước khi làm bất kỳ thay đổi nào:
1. Đọc toàn bộ docs/PLAN.md.
2. Đọc toàn bộ docs/PROJECT_PROGRESS.md.
3. Đọc README.md.
4. Kiểm tra repository hiện tại.
5. Đối chiếu PROJECT_PROGRESS.md với code thực tế; nếu lệch thì sửa progress trước khi tiếp tục.
6. Xác định module liên quan.
7. Không thay đổi architecture ngoài scope nếu không thật sự cần.
8. Không rewrite code đang chạy chỉ để "clean hơn".
9. Không hardcode secret, token, API key, product ID hoặc user ID.
10. External services phải dùng adapter/interface và phải có mock implementation.
11. Omnichannel integrations như Grab/marketplace/social không được hardcode vào core business logic.
12. Phải phân biệt gross revenue, platform fees, merchant discount và net settlement.
13. External attribution phải ghi rõ confidence: DETERMINISTIC / INFERRED / AGGREGATED / UNKNOWN.
14. Không được coi outbound click sang marketplace là confirmed purchase nếu không có conversion/order mapping đáng tin cậy.
15. Mọi API phải có validation, error handling và permission phù hợp.
16. Mọi UI phải có loading, empty, error và success states.
17. Mọi thay đổi DB phải dùng migration.
18. Sau khi code xong phải chạy:
   - lint
   - typecheck
   - unit tests
   - integration tests liên quan
   - build
19. Nếu test/build lỗi, tự sửa trước khi kết thúc.
20. Update docs nếu thay đổi behavior, API hoặc data model.
21. Cuối task:
   - Bắt buộc cập nhật docs/PROJECT_PROGRESS.md trước.
   - Sau đó báo cáo:
     - Files changed
     - DB migrations
     - API added/changed
     - Tests added
     - Commands run
     - Known limitations
     - Current progress
     - Next recommended task

Không tạo fake implementation trong production path.
Không bỏ TODO mơ hồ.
Không claim hoàn thành nếu build/test chưa chạy.

Bây giờ hãy đọc docs/PLAN.md và repository, sau đó tóm tắt kiến trúc hiện tại trong tối đa 20 dòng. Chưa code cho đến khi hiểu cấu trúc.
```

---

# PROMPT 01 — Bootstrap Repository

```text
Dựa trên docs/PLAN.md, hãy bootstrap project theo kiến trúc modular monorepo.

Mục tiêu:
- apps/admin-web: Next.js + TypeScript
- apps/storefront-web: Next.js + TypeScript
- apps/api: FastAPI
- workers/marketing-worker
- packages/ui
- packages/contracts
- infra
- docs

Yêu cầu:
1. Docker Compose cho PostgreSQL, Redis, MinIO và các app cần thiết.
2. .env.example đầy đủ nhưng không có secrets thật.
3. Health check cho API.
4. Basic shared configuration.
5. Lint/format/typecheck.
6. README hướng dẫn chạy local.
7. One-command local startup nếu khả thi.
8. Không build feature business ở prompt này.

Acceptance:
- Developer clone repo mới có thể chạy stack local.
- API health hoạt động.
- Hai Next.js app render được shell cơ bản.
- Postgres/Redis/MinIO healthy.
- lint/typecheck/build pass.

Sau khi hoàn thành hãy cập nhật README và báo cáo commands đã chạy.
```

---

# PROMPT 02 — Authentication + RBAC

```text
Implement authentication và RBAC theo docs/PLAN.md.

Backend:
- User, Role, Permission tables.
- Alembic migrations.
- Password hashing.
- JWT access token.
- Refresh token với rotation/revocation.
- Login/logout/refresh/me endpoints.
- Permission dependency/middleware.
- Seed roles: ADMIN, OWNER, MARKETING, SALES, INVENTORY.

Permissions tối thiểu:
product.read
product.write
inventory.read
inventory.write
order.read
order.update
customer.read
campaign.create
campaign.approve
content.create
content.approve
content.publish
analytics.read
settings.manage
user.manage

Frontend admin:
- Login page.
- Auth session handling.
- Protected routes.
- Permission-aware navigation.
- Unauthorized page.

Security:
- Rate limit auth endpoint.
- Không log password/token.
- Token expiry rõ ràng.

Testing:
- Login success/fail.
- Refresh.
- Permission denied.
- Revoked token.

Acceptance:
- Mỗi role chỉ thấy menu phù hợp.
- API thật sự enforce permission, không chỉ ẩn UI.
```

---

# PROMPT 03 — Admin Design System & App Shell

```text
Build admin UI foundation theo brand Mộc Healthy.

Design:
- Clean white / soft gray background.
- Deep green primary.
- Light green secondary.
- Amber warning.
- Red destructive only.
- Rounded cards.
- Desktop-first admin.
- Responsive.

Build:
- Sidebar.
- Topbar.
- Breadcrumb.
- Global page header.
- Search placeholder.
- Notification button.
- User menu.
- Reusable:
  Button
  Input
  Select
  Dialog
  Drawer
  DataTable
  Pagination
  Badge
  EmptyState
  ErrorState
  Skeleton
  ConfirmDialog
  StatCard
  ChartCard

Menu:
Dashboard
Products
Orders
Customers
Marketing
AI Studio
Content
Analytics
Automation
Settings

Respect RBAC.

Do not implement business pages yet beyond placeholders.

Acceptance:
- Consistent shell.
- Dark/light mode is NOT required unless already planned.
- No layout shift.
- Accessibility basics.
- No TypeScript errors.
```

---

# PROMPT 04 — Product & Category Backend

```text
Implement Product và Category backend.

Use the exact product concepts from docs/PLAN.md.

Product:
- sku
- slug
- name
- descriptions
- category
- base_price
- sale_price
- cost_price
- unit
- status
- featured
- tags
- ingredients
- storage_note
- shelf_life
- SEO fields
- media relationship

Category:
- name
- slug
- description
- sort_order
- active

Features:
- CRUD.
- Search.
- Filter.
- Sort.
- Pagination.
- Bulk status.
- Unique validation.
- sale_price <= base_price.
- Audit price changes.
- OpenAPI docs.

Seed Mộc Healthy demo products listed in PLAN.

Tests:
- CRUD.
- Validation.
- Search/filter.
- permission.
- price rule.

Do not build inventory yet except minimum placeholders if FK requires.
```

---

# PROMPT 05 — Product Admin UI

```text
Build Product Management UI on admin-web using real APIs.

Pages:
- Product list.
- Create product.
- Edit product.
- Product detail.
- Category manager.

Product list:
- Thumbnail.
- Name.
- SKU.
- Category.
- Price.
- Sale price.
- Stock placeholder.
- Status.
- Updated date.
- Actions.

Filters:
- Search.
- Category.
- Status.
- Featured.

UX:
- Server/API pagination.
- Form validation.
- Unsaved-change warning.
- Confirmation for destructive actions.
- Loading/empty/error states.
- Permission-aware edit controls.

Use seed products from Mộc Healthy.

Acceptance:
- Admin can create/edit product without touching DB manually.
- UI refresh reflects API state.
```

---

# PROMPT 06 — Media Upload + Media Library Foundation

```text
Implement media storage abstraction.

Backend:
- MediaAsset table.
- S3-compatible storage adapter.
- MinIO development adapter.
- Upload endpoint.
- Delete/soft-delete.
- Metadata:
  filename
  mime
  size
  width
  height
  duration optional
  type
  tags
  product_id optional
  campaign_id optional
  ai_generated
- Validate MIME and size.
- Generate object key safely.
- Do not expose secret bucket credentials.

Frontend:
- Upload component.
- Image preview.
- Media picker dialog.
- Media Library page basic grid/list.
- Filters by type/tags.

Product:
- Allow thumbnail + gallery using MediaAsset.

Tests:
- Invalid MIME.
- Oversize.
- Permission.
- delete behavior.
```

---

# PROMPT 07 — Inventory & Expiry

```text
Implement batch-based inventory with FEFO.

Models:
InventoryBatch
InventoryMovement

Movement types:
PURCHASE_IN
SALE_OUT
WASTE_OUT
ADJUSTMENT_IN
ADJUSTMENT_OUT
RETURN_IN

Features:
- Receive stock batch.
- expiry_at.
- quantity_received.
- quantity_available.
- supplier optional.
- cost.
- stock summary by product.
- inventory ledger.
- manual adjustment with reason.
- waste.
- low-stock threshold.
- expiry risk query.
- FEFO allocation service.

Admin UI:
- Inventory overview.
- Product stock detail.
- Add batch.
- Adjustment.
- Waste.
- Expiring soon.
- Low stock.

Important:
- Never update stock number directly without creating movement.
- Add transaction/locking strategy preventing negative stock.

Tests:
- movement math.
- FEFO.
- concurrent/negative stock protection.
- expiry queries.
```

---

# PROMPT 08 — Promotion Engine

```text
Implement promotion engine.

Types:
PERCENT_DISCOUNT
FIXED_DISCOUNT
FLASH_SALE
BUY_X_GET_Y
COMBO
FREE_SHIPPING
VOUCHER

Support:
- start/end.
- product scope.
- minimum order.
- max discount.
- usage limit.
- usage per customer.
- active status.
- non-stackable default.
- promo code.

Create pure promotion calculation service with deterministic tests.

Admin:
- Promotion list.
- Create/edit.
- Status.
- Preview calculation.
- Product scope selector.

Acceptance:
- Calculation is backend authoritative.
- Client cannot submit final price.
- Expired promotion never applies.
- Full test matrix for common edge cases.
```

---

# PROMPT 09 — Storefront Foundation

```text
Build storefront-web using Mộc Healthy visual identity.

Public pages:
- Home.
- Category.
- Product detail.
- Search.
- Promotion.
- 404.

Home:
- hero
- today's promotion
- best sellers
- trái cây cắt sẵn
- nước ép/sinh tố
- sữa chua
- combo
- reviews placeholder
- healthy content placeholder

Use real Product API.

Requirements:
- Mobile-first customer experience.
- Fast image loading.
- SEO metadata.
- Structured URLs.
- Skeleton/error/empty states.
- Product cards inspired by Mộc Healthy product presentation.
- Do not clone Grab UI exactly.

Acceptance:
- Products loaded from backend.
- Category/search works.
- Lighthouse basics considered.
```

---

# PROMPT 10 — Cart + Checkout

```text
Implement cart and checkout.

Cart:
- guest cart.
- authenticated cart if user auth exists.
- add/remove/update quantity.
- server recalculates price.
- promotion/voucher.
- cart persistence.
- cart expiration strategy.

Checkout:
- customer name.
- phone.
- delivery address.
- note.
- payment method:
  COD
  BANK_TRANSFER
- final order summary.
- terms/consent.

Security:
- Never trust client totals.
- Validate product availability.
- Validate promotion again at checkout.

Tracking hooks:
- add_to_cart
- remove_from_cart
- begin_checkout
- apply_coupon

Tests:
- price recalculation.
- unavailable product.
- expired promotion.
- duplicate submission/idempotency.
```

---

# PROMPT 11 — Order Management

```text
Implement order lifecycle.

Statuses:
NEW
CONFIRMED
PREPARING
READY
SHIPPING
COMPLETED
CANCELLED
REFUNDED

Backend:
- Order.
- OrderItem.
- OrderStatusHistory.
- Payment placeholder.
- Source.
- Idempotent create order.
- Inventory reservation/deduction strategy.
- Cancel behavior.
- Audit status change.

Admin:
- Order list.
- Filters.
- Detail.
- Customer info.
- Items.
- Status timeline.
- Internal note.
- Status update.

Storefront:
- Order confirmation.
- Order lookup/tracking.

Test full lifecycle.

Acceptance:
Customer can place order → admin complete order.
```

---

# PROMPT 11A — Omnichannel Order Hub + Marketplace Import

```text
Extend Order Management into an omnichannel order hub.

Goal:
Mộc must manage orders/revenue from WEBSITE + external marketplaces such as Grab without coupling business logic to one provider.

Backend:
1. Add/verify Order fields:
   channel
   external_order_id
   external_store_id
   gross_amount
   merchant_discount
   platform_discount
   platform_fee
   shipping_fee
   other_fee
   net_amount
   ordered_at
   settled_at
   raw_import_id

2. Add unique idempotency rule:
   (channel, external_order_id)

3. Create OrderProvider abstraction:
   fetch_orders
   fetch_order_detail
   fetch_settlements
   validate_connection
   normalize_order

4. Implement:
   WebsiteOrderProvider
   MockMarketplaceProvider
   ManualImportOrderProvider

5. Create MarketplaceImport:
   provider
   file
   status
   imported_rows
   rejected_rows
   duplicate_rows
   timestamps
   error report

6. Build CSV/XLSX import:
   upload
   preview
   validate
   map columns
   normalize
   duplicate detection
   transaction-safe import

Admin:
- Omnichannel order filters.
- Channel badges.
- Import Marketplace Report screen.
- Import preview/result.
- Gross vs net values.
- External order reference.

Important:
- Do not fake a Grab API.
- If real API credentials/documentation are unavailable, import path + mock provider must work completely.
- Never equate net settlement with gross revenue.

Tests:
- idempotent import.
- duplicate detection.
- invalid rows.
- mixed channels.
- gross/net calculations.
```

---

# PROMPT 12 — Customer CRM + Customer 360

```text
Implement Customer CRM.

Backend:
Customer
CustomerAddress
CustomerTag
CustomerSegment

Computed:
- order_count
- total_spent
- average_order_value
- first_order_at
- last_order_at

Rule segments:
NEW
ACTIVE
REPEAT
VIP
AT_RISK
DORMANT
HIGH_VALUE
PROMO_SENSITIVE

Admin:
- Customer list.
- Search.
- Filter segment.
- Customer 360 page:
  profile
  orders
  spend
  favorite products
  favorite category
  source
  tags
  timeline

Add marketing consent fields.

Do not send PII to AI.

Tests:
- metrics.
- segment rules.
- permission.
```

---

# PROMPT 13 — Event Tracking Foundation

```text
Implement first-party event tracking.

Create TrackingEvent model and ingestion API.

Fields:
event_name
anonymous_id
user_id optional
session_id
timestamp
page_url
referrer
utm_source
utm_medium
utm_campaign
utm_content
product_id
order_id
campaign_id
metadata

Events:
page_view
product_view
category_view
search
promotion_view
add_to_cart
remove_from_cart
begin_checkout
apply_coupon
purchase
content_click
campaign_click
social_referral
customer_login
customer_signup
review_submitted

Frontend:
- lightweight tracking client.
- session/anonymous id.
- safe batching if useful.
- no PII in metadata.

Acceptance:
- Storefront actions create trackable events.
- purchase event ties order and attribution.
```

---

# PROMPT 13A — Smart Link + External Attribution

```text
Implement Mộc Smart Link for ads that send customers to Website, Grab, Zalo or another external sales channel.

Backend models:
SmartLink
SmartLinkClick

Route:
GET /r/{slug}

Flow:
1. Resolve active SmartLink.
2. Generate click_id.
3. Store click event.
4. Preserve source/medium/campaign/content metadata.
5. Return safe 302/307 redirect to configured destination.

Admin:
- Smart Link list.
- Create/edit.
- Link to campaign/product/content.
- Destination channel.
- Copy generated URL.
- Click statistics.

Tracking:
- outbound_click event.
- campaign/source/content.
- destination channel.

Attribution:
Add attribution confidence:
DETERMINISTIC
INFERRED
AGGREGATED
UNKNOWN

Rules:
- A Smart Link click to Grab is NOT proof of purchase.
- Never mark external revenue deterministic without a reliable conversion/order mapping.
- Support mapping internal campaign ↔ promo code ↔ external campaign reference.

Security:
- Validate redirect URL.
- Prevent open redirect abuse.
- Do not store unnecessary PII.
- Rate-limit abusive traffic where appropriate.

Tests:
- valid redirect.
- inactive/expired link.
- invalid destination.
- event created once.
- UTM preservation.
```

---

# PROMPT 14 — Attribution + Analytics Base

```text
Implement analytics foundation.

Attribution MVP:
- first touch.
- last touch.

Build materialized/query services as appropriate for:
- revenue by day.
- orders by day.
- revenue by source.
- orders by source.
- conversion funnel.
- product revenue.
- category revenue.
- new vs returning customer.

API endpoints:
- analytics/overview
- analytics/revenue
- analytics/sources
- analytics/funnel
- analytics/products

Admin dashboard:
- date filter.
- KPI cards.
- charts with ECharts.
- compare previous period.

Use database queries, not AI, for metrics.

Tests:
- analytics numbers against deterministic fixture data.
```

---

# PROMPT 15 — Campaign Management

```text
Implement Campaign module.

Fields:
name
objective
status
start_at
end_at
budget
target_audience
products
channels
promotion
landing_page
owner
notes

Objectives:
AWARENESS
TRAFFIC
CONVERSION
REMARKETING
RETENTION
INVENTORY_CLEARANCE
NEW_PRODUCT

Statuses:
DRAFT
PLANNING
READY_FOR_REVIEW
APPROVED
ACTIVE
PAUSED
COMPLETED
CANCELLED

Workflow:
create
edit
submit review
approve/reject
activate
pause
complete

Approval requires permission campaign.approve.

Admin:
- list
- create wizard
- detail
- performance placeholder
- approval history

Audit approvals.
```

---

# PROMPT 16 — Content Model + Review Workflow

```text
Implement content management before AI generation.

Models:
ContentItem
ContentVersion
ContentApproval

Fields per PLAN.

Statuses:
DRAFT
AI_GENERATED
IN_REVIEW
APPROVED
SCHEDULED
PUBLISHING
PUBLISHED
FAILED
ARCHIVED

Build:
- create content manually.
- edit creates version.
- submit review.
- approve/reject.
- rollback/view old versions.
- attach media.
- campaign/product association.

Admin:
- content library.
- editor.
- version history.
- review queue.

Permissions:
content.create
content.approve
content.publish

Tests:
- invalid status transitions.
- approval permission.
- versioning.
```

---

# PROMPT 17 — Content Calendar

```text
Build Content Calendar using real ContentItem data.

Views:
- month
- week
- day

Filters:
- channel
- campaign
- product
- status

Actions:
- drag/drop reschedule
- duplicate
- approve if permitted
- schedule
- unschedule
- publish now placeholder

Display:
- thumbnail
- title
- channel
- time
- status

Backend:
- scheduling fields.
- conflict validation if needed.
- timezone-safe datetime.

Use Asia/Ho_Chi_Minh display by default while storing UTC.

Tests:
- schedule.
- reschedule.
- timezone.
- permission.
```

---

# PROMPT 18 — Social Provider Abstraction + Mock Publisher

```text
Implement social publishing architecture without relying on real platform approval.

Create SocialProvider interface:
- validate_connection
- publish_text
- publish_image
- publish_video
- fetch_post_metrics
- refresh_token

Create:
- MockSocialProvider
- WebsitePublisher

Models:
SocialConnection
PublishedPost
PostMetric

Queue flow:
APPROVED
→ SCHEDULED
→ queued
→ PUBLISHING
→ PUBLISHED / FAILED

Worker:
- pickup due content.
- publish.
- retry exponential backoff.
- max retry.
- store error.
- idempotency.

Admin:
- Social Connections page.
- Mock connection.
- Publish logs.

Acceptance:
End-to-end schedule → worker → mock published record.
```

---

# PROMPT 19 — AI Provider Abstraction

```text
Implement AI provider abstraction.

Interface:
- generate_text
- generate_json
- analyze
- health_check

Requirements:
- provider configured through env.
- prompt version stored.
- token/cost metadata if provider exposes it.
- timeout.
- retry.
- structured output validation with Pydantic.
- no raw customer PII.

Models:
AIGenerationLog
PromptTemplate or prompt version storage.

Create MockAIProvider for tests.

Do not implement user-facing AI features yet except a protected test endpoint/admin health indicator.

Tests:
- structured JSON success.
- malformed output.
- timeout.
- retry.
- provider unavailable.
```

---

# PROMPT 20 — AI Content Studio

```text
Build AI Content Studio.

Input:
- product
- campaign
- audience
- promotion
- brand tone
- channels
- desired formats

Generate content pack:
Facebook:
- caption
- CTA

Instagram:
- caption
- hashtags
- reel idea

TikTok:
- hook
- 15-30s script
- shot list
- CTA

Zalo:
- short promotional message

Website:
- banner title
- banner subtitle
- CTA

Optional:
- SEO product description
- image generation brief

Rules:
- Use real product facts from DB.
- Never invent price or promotion.
- Validate outputs.
- Save each output as ContentItem with AI_GENERATED status.
- User can edit before submit review.

UI:
- source product panel.
- campaign context.
- channel toggles.
- generation progress.
- preview tabs.
- regenerate one channel.
- save all.

Acceptance:
One button can create a multi-channel content pack.
```

---

# PROMPT 21 — AI Marketing Strategist

```text
Implement AI Marketing Strategist using deterministic business data + AI explanation.

Step 1:
Backend computes evidence:
- product sales trend.
- inventory quantity.
- expiry risk.
- campaign performance.
- channel performance.
- customer segment stats.

Step 2:
Send only necessary aggregate evidence to AI.

Output schema:
title
problem
evidence[]
recommended_action
products[]
customer_segment
channels[]
promotion{}
suggested_schedule[]
expected_metric
confidence
risks
insufficient_data

Hard rules:
- AI cannot invent metrics.
- Every numeric claim must exist in evidence.
- If insufficient data, return insufficient_data=true.
- AI recommendation is advisory.

Build:
- Recommendations page.
- Generate recommendation.
- Link to evidence.
- Convert recommendation → Campaign draft.

Tests:
- evidence mismatch rejection.
- insufficient data.
- JSON validation.
```

---

# PROMPT 22 — CEO Dashboard + AI Insights

```text
Complete CEO Dashboard.

KPI:
Revenue
Orders
AOV
Conversion Rate
New Customers
Returning Customers
Repeat Purchase Rate
Marketing Spend if available
CAC if available
ROAS if available
Gross Profit if cost data reliable

Charts:
Revenue trend
Orders trend
Revenue by category
Top products
Revenue by source
Funnel
Customer mix
Inventory risk

AI Insight:
- Separate section.
- Must show date range.
- evidence references.
- recommended action.
- confidence.
- link to create campaign if relevant.

Do not let AI calculate core financial metrics.
All financial numbers come from backend queries.
```

---

# PROMPT 23 — Automation Engine Foundation

```text
Implement generic Marketing Automation engine.

Concepts:
Workflow
Trigger
Condition
Action
Wait
Run
StepRun

Initial triggers:
CUSTOMER_CREATED
CART_ABANDONED
ORDER_COMPLETED
CUSTOMER_INACTIVE
INVENTORY_EXPIRY_RISK
LOW_STOCK
CAMPAIGN_ENDING

Actions:
CREATE_NOTIFICATION
CREATE_RECOMMENDATION
CREATE_CAMPAIGN_DRAFT
SEND_EMAIL_MOCK
SEND_ZALO_MOCK
ADD_CUSTOMER_TAG
WAIT

Build:
- workflow CRUD.
- enable/disable.
- execution engine.
- run history.
- per-step logs.
- retry.
- idempotency.

Admin:
- workflow list.
- basic builder or form-based editor.
- runs.
- errors.

Do NOT build a complex visual node editor yet.
```

---

# PROMPT 24 — Initial Automation Templates

```text
Create production-ready workflow templates.

1. Welcome Flow
Customer created
→ marketing consent?
→ welcome
→ optional first-order promotion

2. Abandoned Cart
cart inactive for configured hours
→ no purchase?
→ reminder
→ stop if purchased

3. Repeat Purchase
order completed
→ wait configurable days
→ suggest related product

4. Reactivation
no purchase X days
→ tag AT_RISK
→ create reactivation action

5. Inventory Clearance Recommendation
expiry risk + quantity threshold
→ create AI recommendation
→ notify OWNER
→ owner decides whether to create campaign

Important:
- Do not auto-discount inventory without human approval.
- Every automation run is auditable.
```

---

# PROMPT 25 — Alerts & Notification Center

```text
Implement alerts and notification center.

Alert types:
LOW_STOCK
EXPIRY_RISK
HIGH_WASTE
REVENUE_ANOMALY
CONVERSION_DROP
ROAS_DROP
PUBLISH_FAILED
PROVIDER_AUTH_EXPIRED
QUEUE_FAILURE
AI_PROVIDER_ERROR
CAMPAIGN_ENDING

Features:
- severity.
- deduplication.
- read/unread.
- resolve.
- entity link.
- created_at/resolved_at.

Admin:
- bell count.
- notification drawer.
- alerts page.
- filters.

Create in-app first.
Email adapter may be mock/configurable.

Tests:
- dedup.
- read.
- resolve.
- permission.
```

---

# PROMPT 26 — Real Social Integrations Scaffold

```text
Prepare real social provider integrations without breaking the mock path.

Implement provider classes/configuration for:
- Meta / Facebook + Instagram
- TikTok
- Zalo
- Google Business if applicable

Important:
1. Read official provider API requirements before implementation.
2. Keep credentials in secrets/env.
3. OAuth/token refresh architecture.
4. Connection validation.
5. Store scopes and expiry.
6. Feature capability matrix because platforms differ.
7. If a provider/account does not support scheduling directly, keep our internal scheduler and publish at due time.
8. Do not fake success.

Admin:
- Connect.
- Connection status.
- scopes.
- token expiry.
- disconnect.

If credentials are unavailable:
- code adapter and integration tests with mocks.
- keep MockSocialProvider usable.
- document exact setup steps for production credentials.
```

---

# PROMPT 27 — Post Metrics Sync

```text
Implement PostMetric synchronization.

Metrics where available:
impressions
reach
views
clicks
likes
comments
shares
saves
watch_time
engagement

Worker:
- periodic sync.
- platform capability mapping.
- upsert.
- error handling.

Analytics:
- content performance.
- channel performance.
- best content by selected metric.
- normalize metric names without pretending unavailable metrics exist.

Link:
PublishedPost
→ ContentItem
→ Campaign
→ product

Acceptance:
Campaign/content page can display organic performance data.
```

---

# PROMPT 28 — Marketing Spend / Ads Analytics

```text
Implement ad performance data model and analytics.

Models:
AdAccount
AdCampaignMetric

Fields:
date
provider
external_campaign_id
campaign_id optional
spend
impressions
clicks
conversions
revenue_attributed

MVP:
- manual import/API endpoint/CSV importer if provider APIs unavailable.
- analytics formulas:
  CTR
  CPC
  CPA/CAC where valid
  ROAS

Admin:
- ad performance.
- campaign comparison.
- spend vs revenue.

Rules:
- Avoid division-by-zero.
- Clearly label estimated/attributed metrics.
- Do not let AI alter budget.

Later provider sync should plug into the same model.
```

---

# PROMPT 28A — Marketplace Settlement & Revenue Reconciliation

```text
Implement financial reconciliation for external marketplaces.

Models:
Settlement
SettlementOrder

Settlement fields:
provider
external_settlement_id
period_start
period_end
gross_amount
platform_fee
merchant_discount
other_fee
net_amount
paid_at
status

Reconciliation statuses:
UNMATCHED
PARTIAL
MATCHED
DISPUTED

Features:
- Import settlement CSV/XLSX.
- Match settlement lines to normalized orders.
- Show unmatched orders.
- Show unmatched settlement rows.
- Manual reconciliation with audit.
- Reconciliation summary by period/channel.

Analytics:
- gross revenue.
- platform fees.
- promotion cost.
- net settlement.
- net revenue/order.
- gross vs net by channel.

Campaign attribution:
- deterministic revenue separated from inferred/aggregated revenue.
- map promo code/external campaign ref where available.

CEO dashboard:
Add channel table:
orders
gross
fees
net
AOV
net/order
attribution confidence

AI:
May summarize reconciliation results but must never convert inferred attribution into exact conversion claims.

Tests:
- exact match.
- partial match.
- duplicate settlement.
- disputed row.
- net math.
- period summary.
```

---

# PROMPT 29 — AI Campaign Generator

```text
Build "Create Campaign with AI" workflow.

Entry points:
- from AI recommendation.
- manual AI Studio.

Input:
- objective.
- target product(s).
- audience.
- channels.
- promotion constraints.
- date range.
- planned budget optional.

AI proposes:
- campaign name.
- value proposition.
- audience summary.
- channel strategy.
- content themes.
- posting schedule.
- content pack brief.
- KPI target suggestions clearly labeled as suggestions.

Then user can:
EDIT
SAVE DRAFT
SUBMIT REVIEW

After campaign approval:
Generate Content Pack.

Do NOT automatically activate ads or change prices.

Acceptance:
Recommendation → campaign draft → approval → content generation works end-to-end.
```

---

# PROMPT 30 — Closed-loop Marketing End-to-End

```text
Implement and verify the complete closed-loop scenario.

Scenario:
1. Seed historical sales.
2. Seed Dưa lưới inventory with high quantity / expiry risk.
3. Analytics computes evidence.
4. AI Strategist generates inventory clearance recommendation.
5. OWNER opens recommendation.
6. Click Create Campaign.
7. AI Campaign Generator creates draft.
8. OWNER/MARKETING edits and submits.
9. Authorized user approves.
10. AI Content Studio creates content pack.
11. Content gets reviewed/approved.
12. Schedule Facebook + TikTok + Website using MockSocialProvider.
13. Worker publishes at due time.
14. Tracking events simulate customer click.
15. Customer purchases via storefront.
16. Order completes.
17. Attribution ties conversion to campaign.
18. Dashboard updates revenue/channel/campaign.
19. AI analysis summarizes result using real metrics.

Create:
- seed/demo script for this scenario.
- automated integration/E2E tests where practical.
- docs/DEMO_FLOW.md.

Acceptance:
This full scenario can be demonstrated locally without manually editing database.
```

---

# PROMPT 31 — Reviews + Loyalty

```text
Implement Reviews and basic Loyalty.

Reviews:
- verified-order review option.
- rating.
- text.
- moderation status.
- storefront display.
- admin moderation.

Loyalty:
- points ledger.
- points earned from completed order.
- configurable rate.
- redemption disabled initially unless implemented end-to-end.
- admin customer points history.

Do not add complex membership tiers yet.

Tests:
- no duplicate points.
- cancelled/refunded behavior.
```

---

# PROMPT 32 — SEO + Content Marketing

```text
Implement SEO content foundation.

Product:
- title/meta.
- canonical.
- structured data.

Category:
- SEO title/description.

Blog:
- post.
- category.
- slug.
- status.
- author.
- cover.
- SEO.
- publish date.

AI Studio:
- outline.
- draft.
- SEO title.
- meta description.

Rules:
AI drafts require human review before publish.

Storefront:
- sitemap.
- robots.
- metadata.
- OpenGraph.
- product structured data where appropriate.

Acceptance:
No duplicate metadata in seed pages.
```

---

# PROMPT 33 — Global Search

```text
Implement global admin search.

Search entities:
- product.
- order.
- customer.
- campaign.
- content.

Features:
- command palette.
- keyboard shortcut.
- permission filtering.
- fast response.
- exact order lookup.
- product/customer fuzzy search if practical.

No external search service required unless data volume justifies it.
```

---

# PROMPT 34 — Audit Log UI

```text
Complete AuditLog system.

Backend:
Ensure critical mutations log:
- product price.
- promotion.
- inventory adjustment.
- order status manual override.
- campaign approval.
- content approval.
- publish.
- role/permission.
- provider connection.
- system config.

Admin:
- searchable audit log.
- user.
- action.
- entity.
- date.
- before/after viewer.

Only ADMIN/OWNER as configured can view.
```

---

# PROMPT 35 — Security Hardening

```text
Perform application security hardening.

Review:
- authentication.
- refresh token.
- cookie/token storage.
- CORS.
- CSRF if applicable.
- rate limits.
- upload security.
- access control.
- IDOR.
- SQL injection.
- XSS.
- secrets.
- error leakage.
- logs.
- dependency vulnerabilities.
- AI prompt injection exposure.
- SSRF if URLs can be imported.

Implement fixes.

Add docs/SECURITY.md:
- threat model summary.
- secret handling.
- production checklist.
- incident basics.

Do not expose real secrets in report.
```

---

# PROMPT 36 — Performance & Database Review

```text
Perform performance review with realistic seed data.

Check:
- N+1 queries.
- indexes.
- pagination.
- analytics query cost.
- dashboard query count.
- image delivery.
- Redis opportunities.
- background jobs.
- frontend bundle.
- long lists.

Add DB indexes only with evidence.
Add caching only where invalidation is clear.

Create benchmark notes in docs/PERFORMANCE.md.
```

---

# PROMPT 37 — Backup & Restore

```text
Implement/document backup strategy.

PostgreSQL:
- automated backup script.
- retention config.
- restore script.
- verification steps.

Object storage:
- backup strategy.
- restore notes.

Create:
infra/scripts/backup
infra/scripts/restore

Add docs/BACKUP_RESTORE.md.

Acceptance:
Perform at least one local backup → restore test to a fresh local database and document result.
```

---

# PROMPT 38 — CI/CD

```text
Create CI pipeline.

For PR:
- backend lint.
- backend tests.
- frontend lint.
- frontend typecheck.
- frontend tests.
- builds.

For release:
- docker images.
- migration check.
- deployment artifact.

Add:
- branch protection recommendations.
- environment separation:
  dev
  staging
  prod

No production credentials in CI config.
```

---

# PROMPT 39 — Production Deployment

```text
Prepare production deployment architecture.

Target:
- Docker-based deployment.
- reverse proxy.
- TLS.
- PostgreSQL.
- Redis.
- object storage.
- API.
- admin.
- storefront.
- worker.

Create:
- production compose or deployment manifests appropriate for current infrastructure.
- nginx/reverse proxy config.
- health checks.
- restart policy.
- log persistence/rotation.
- migration procedure.
- rollback procedure.
- docs/DEPLOYMENT.md.

Do not use Kubernetes unless there is a concrete requirement.
```

---

# PROMPT 40 — Final Product QA

```text
Perform full product QA against docs/PLAN.md.

Create a requirement traceability checklist:
Requirement → Implementation → Test → Status.

Validate end-to-end:
1. Auth/RBAC.
2. Product.
3. Inventory.
4. Promotion.
5. Storefront.
6. Cart.
7. Checkout.
8. Order.
9. Customer 360.
10. Tracking.
11. Analytics.
12. Campaign.
13. Content.
14. Calendar.
15. AI Content.
16. AI Strategist.
17. Publisher.
18. Automation.
19. Alerts.
20. CEO dashboard.
21. Audit.
22. Backup.
23. Security.

Run:
- all linters.
- typecheck.
- unit tests.
- integration tests.
- E2E.
- production builds.

Fix P0/P1 bugs found.

Generate:
docs/QA_REPORT.md

Do not mark DONE with failing tests.
```

---

# PROMPT 41 — UX Polish

```text
Perform final UX review focused on actual store operations.

Audit:
- Can owner find today's important issue within 30 seconds?
- Can staff create/edit product quickly?
- Can staff process an order with minimal clicks?
- Can marketer create one campaign without understanding technical details?
- Can user distinguish AI suggestion from confirmed business fact?
- Are dangerous actions clearly confirmed?
- Are tables usable on 1366px laptop?
- Is storefront excellent on mobile?
- Are all empty/error/loading states helpful?

Fix usability issues without redesigning architecture.
```

---

# PROMPT 42 — Final Documentation & Handover

```text
Prepare technical + operational handover.

Update/create:
README.md
docs/PLAN.md
docs/ARCHITECTURE.md
docs/DATA_MODEL.md
docs/API.md
docs/EVENT_TAXONOMY.md
docs/SECURITY.md
docs/BACKUP_RESTORE.md
docs/DEPLOYMENT.md
docs/DEMO_FLOW.md
docs/OPERATIONS.md
docs/QA_REPORT.md

OPERATIONS must explain:
- start/stop.
- create admin.
- connect social account.
- configure AI.
- backup/restore.
- inspect failed jobs.
- retry publish.
- rotate credential.
- common errors.

Verify docs match code.
```

---

# PROMPT 43 — Final Release Gate

```text
Treat this as release gate for Mộc Healthy v1.

Do not add new features.

Only:
- inspect.
- test.
- fix blockers.
- document residual risk.

Release criteria:
- zero failing critical test.
- zero known P0 bug.
- production build success.
- migrations work from clean DB.
- backup restore verified.
- owner user can complete closed-loop demo.
- secrets not committed.
- mock providers cannot accidentally be used in production unless explicitly configured.
- monitoring/health endpoints work.
- documentation complete.

Return:
1. PASS/FAIL by criterion.
2. Remaining P1/P2 issues.
3. Production launch checklist.
4. Exact release command/process.
```

---

# Reusable Prompt — Fix a Bug

```text
Investigate this bug as a senior engineer.

Before editing:
1. Reproduce.
2. Find root cause.
3. Identify whether similar code paths are affected.
4. Add regression test that fails before the fix.
5. Implement the smallest correct fix.
6. Run related tests + lint/typecheck/build if affected.

Do not:
- silence exceptions.
- remove validation.
- weaken types.
- add arbitrary sleeps.
- catch Exception without handling.
- hardcode a special-case ID.

Bug:
[PASTE BUG HERE]
```

---

# Reusable Prompt — Review a Feature

```text
Review the following feature against docs/PLAN.md as Principal Engineer.

Check:
- correctness.
- business logic.
- security.
- permission.
- validation.
- DB integrity.
- concurrency.
- failure handling.
- UX states.
- tests.
- maintainability.
- observability.

Do not rewrite working code unless an issue is concrete.

Return issues grouped:
P0 blocker
P1 important
P2 improvement

Then fix P0/P1 and add tests.

Feature:
[FEATURE NAME]
```

---

# Reusable Prompt — Database Migration Review

```text
Review this DB migration for production safety.

Check:
- backwards compatibility.
- locking.
- default values.
- nullability.
- index build impact.
- data migration.
- rollback.
- deploy order between app and migration.

If risky, propose a multi-step migration strategy.

Migration:
[PASTE / POINT TO FILE]
```

---

# Reusable Prompt — UI Screen

```text
Build/refine this screen using the existing Mộc Healthy design system.

Requirements:
- Use existing components before creating new ones.
- Respect RBAC.
- Real API, no hardcoded production data.
- Loading skeleton.
- Empty state.
- Error state.
- Validation.
- Responsive.
- Keyboard/accessibility basics.
- No arbitrary colors outside design tokens.
- Do not change unrelated pages.

Screen:
[SCREEN NAME]

Business purpose:
[WHY IT EXISTS]

Actions:
[ACTIONS]

Data:
[DATA]
```

---

# Reusable Prompt — AI Feature Safety Review

```text
Review this AI feature for correctness and business safety.

Verify:
- no invented product facts.
- no invented price.
- no invented stock.
- no invented revenue metrics.
- evidence exists for analytical claims.
- PII minimized.
- structured outputs validated.
- prompt/version logged.
- timeout/retry.
- user can distinguish AI suggestion vs system fact.
- autonomous actions require correct approval.
- failures do not corrupt business data.

Feature:
[AI FEATURE]
```

---

# Reusable Prompt — End-of-Session Checkpoint

```text
Before ending this coding session:

1. Run relevant lint/typecheck/tests/build.
2. Review git diff for accidental changes.
3. Check migrations.
4. Check no secrets were added.
5. Remove debug logs.
6. Update relevant docs.
7. Update `docs/PROJECT_PROGRESS.md` and make sure it matches the actual repository:
   - current phase
   - current prompt
   - status
   - progress %
   - acceptance criteria
   - files changed
   - commands run
   - tests/build
   - blockers
   - technical debt
   - DB/API changes
   - next action
8. Summarize:
   - completed
   - not completed
   - known issue
   - current progress
   - next exact prompt/task
9. Suggest a concise git commit message.

End your response with:
Progress file updated: YES
Current phase: ...
Current prompt: ...
Status: ...
Next prompt: ...

Do not start a new feature.
```

---

# Recommended Git Milestones

```text
milestone/00-foundation
milestone/01-commerce-core
milestone/02-crm-analytics
milestone/03-marketing
milestone/04-ai-content
milestone/05-social-publishing
milestone/06-ai-recommendation
milestone/07-automation
milestone/08-production
```

---

# Khi nào hệ thống được xem là "hoàn thành v1"

Hệ thống chỉ đạt v1 khi demo được liên tục:

```text
Product
→ Inventory
→ AI Recommendation
→ Campaign
→ AI Content
→ Review
→ Approval
→ Schedule
→ Publish
→ Customer Visit
→ Cart
→ Checkout
→ Order
→ Attribution
→ Analytics
→ AI Result Analysis
```

và toàn bộ luồng trên:
- dùng dữ liệu thực trong DB,
- không cần chỉnh DB thủ công,
- có audit,
- có tests,
- có error handling,
- có tài liệu vận hành.
