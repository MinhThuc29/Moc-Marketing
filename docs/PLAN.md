# MỘC HEALTHY — AI MARKETING & COMMERCE PLATFORM
## Master Product & Technical Plan for Vibe Coding
> **Revision 2026-10-01:** mở rộng kiến trúc thành Omnichannel Commerce Hub, hỗ trợ quản lý doanh thu từ Website + Grab + các marketplace khác, Smart Link, external attribution và settlement reconciliation.


> Mục tiêu của tài liệu này là làm **single source of truth** cho toàn bộ quá trình phát triển hệ thống Mộc Healthy.  
> Khi vibe code bằng Cursor / Claude Code / Codex / Antigravity / Copilot Agent, luôn yêu cầu agent đọc file này trước khi thay đổi kiến trúc hoặc code.

---

# 0. Executive Summary

Mộc Healthy hiện bán:
- Trái cây cắt sẵn.
- Nước ép.
- Sinh tố.
- Sữa chua.
- Matcha / đồ uống healthy.
- Combo / khuyến mãi.

Mục tiêu không chỉ là tạo một website bán hàng mà là xây dựng một **AI Marketing & Commerce Platform** có khả năng:

1. Quản lý sản phẩm, kho, giá và khuyến mãi.
2. Bán hàng trực tiếp trên website.
3. Quản lý khách hàng và đơn hàng.
4. Tạo nội dung marketing bằng AI.
5. Lập lịch và xuất bản nội dung đa nền tảng.
6. Theo dõi hiệu quả quảng cáo / content / doanh thu.
7. Tự động phân tích dữ liệu và đưa ra recommendation.
8. Dần tiến tới mô hình:
   **AI phân tích → đề xuất campaign → tạo content → chờ duyệt → tự đăng → đo kết quả → tối ưu vòng sau.**

---

# 1. North Star

## 1.1 Vision

Biến Mộc Healthy từ một cửa hàng bán trên các nền tảng bên ngoài thành một hệ thống thương mại số có dữ liệu riêng, khách hàng riêng và năng lực marketing tự động.

## 1.2 North Star Metric

Ưu tiên theo dõi:

- Monthly Revenue.
- Repeat Purchase Revenue.
- Orders from owned channels.
- Conversion Rate.
- Average Order Value.
- Customer Acquisition Cost.
- Customer Lifetime Value.
- ROAS.
- Repeat Purchase Rate.

## 1.3 Công thức tăng trưởng

```text
Traffic
  ×
Conversion Rate
  ×
Average Order Value
  ×
Purchase Frequency
=
Revenue
```

AI và automation phải phục vụ ít nhất một trong bốn biến số trên.

---

# 2. Product Principles

1. **Data first**  
   Mọi chiến dịch, bài đăng, click, add-to-cart, đơn hàng phải đo được.

2. **Human approval before autonomous marketing**  
   Giai đoạn đầu AI không tự thay đổi giá, ngân sách quảng cáo hoặc publish nội dung nhạy cảm nếu chưa được duyệt.

3. **One source → many channels**  
   Một sản phẩm / campaign có thể tạo content riêng cho Facebook, TikTok, Instagram, Zalo, Website.

4. **Không copy y nguyên content giữa các kênh**  
   AI phải format theo platform.

5. **Business action > dashboard đẹp**  
   Dashboard phải trả lời:
   - Điều gì đang xảy ra?
   - Tại sao?
   - Cần làm gì tiếp?

6. **API / provider abstraction**  
   Social API, AI provider, email, storage phải có adapter để thay đổi nhà cung cấp mà không phá business logic.

7. **Build modular monolith first**  
   Không microservice quá sớm. Tách module rõ nhưng deploy đơn giản trong MVP.

---

# 3. Target Users & Roles

## 3.1 Owner / CEO

Có quyền:
- Xem dashboard toàn hệ thống.
- Xem doanh thu / lợi nhuận / marketing.
- Duyệt campaign.
- Duyệt ngân sách.
- Xem AI Insights.
- Xem alert.
- Quản lý user cấp cao.

## 3.2 Marketing

Có quyền:
- Tạo campaign.
- Dùng AI Studio.
- Tạo / sửa content.
- Lên lịch.
- Quản lý channel.
- Xem marketing analytics.

Không mặc định có quyền:
- Thay đổi system settings.
- Xóa đơn hàng.
- Thay đổi quyền user.

## 3.3 Sales / Order Operator

- Quản lý đơn hàng.
- Quản lý customer.
- Cập nhật trạng thái giao hàng.
- Ghi chú đơn.
- Xem lịch sử khách hàng.

## 3.4 Inventory / Store Operator

- Quản lý stock.
- Nhập / điều chỉnh stock.
- Cập nhật expiry.
- Cập nhật trạng thái sản phẩm.

## 3.5 Admin

- Toàn quyền kỹ thuật.
- User / role / permission.
- Provider credentials.
- Audit log.
- System config.

---

# 4. High-Level System Flow

```text
PRODUCT + INVENTORY + CUSTOMER + SALES DATA
                    │
                    ▼
             AI MARKETING ENGINE
                    │
                    ▼
            AI RECOMMENDATION
                    │
                    ▼
                 CAMPAIGN
                    │
                    ▼
            AI CONTENT STUDIO
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    CAPTION       IMAGE        VIDEO SCRIPT
       │            │            │
       └────────────┼────────────┘
                    ▼
                  REVIEW
                    │
                    ▼
                 APPROVE
                    │
                    ▼
                SCHEDULER
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
 FACEBOOK       INSTAGRAM       TIKTOK
      │             │             │
      ├────────── ZALO ───────────┤
      └──────── WEBSITE ──────────┘
                    │
                    ▼
                 CUSTOMER
                    │
                    ▼
             WEBSITE / ORDER
                    │
                    ▼
               SALES DATA
                    │
                    ▼
                ANALYTICS
                    │
                    ▼
              AI ANALYSIS
                    │
                    ▼
             NEXT RECOMMENDATION
```

---

# 5. Information Architecture

Admin sidebar:

```text
Mộc Marketing AI
├── 01 Dashboard
├── 02 Products
├── 03 Orders
├── 04 Customers
├── 05 Marketing
├── 06 AI Studio
├── 07 Content
├── 08 Analytics
├── 09 Automation
└── 10 Settings
```

## 5.1 Dashboard

```text
Dashboard
├── Overview
├── Sales
├── Marketing
├── Customers
└── AI Insights
```

## 5.2 Products

```text
Products
├── Product List
├── Categories
├── Inventory
├── Inventory Movements
├── Promotions
└── Media
```

## 5.3 Orders

```text
Orders
├── All Orders
├── New
├── Confirmed
├── Preparing
├── Shipping
├── Completed
├── Cancelled
└── Refund
```

## 5.4 Customers

```text
Customers
├── Customer List
├── Segments
├── Loyalty
├── Reviews
└── Customer 360
```

## 5.5 Marketing

```text
Marketing
├── Campaigns
├── Promotions
├── Content Calendar
├── Social Channels
├── Advertising
└── Performance
```

## 5.6 AI Studio

```text
AI Studio
├── Marketing Assistant
├── Content Generator
├── Image Generator
├── Video Script
├── SEO Writer
├── Campaign Generator
└── AI Analysis
```

## 5.7 Content

```text
Content
├── Library
├── Posts
├── Drafts
├── Scheduled
├── Published
└── Templates
```

## 5.8 Analytics

```text
Analytics
├── Revenue
├── Product
├── Customer
├── Channel
├── Campaign
├── Content
└── Attribution
```

## 5.9 Automation

```text
Automation
├── Workflows
├── Triggers
├── Runs
├── Alerts
└── Templates
```

## 5.10 Settings

```text
Settings
├── Users
├── Roles & Permissions
├── Store
├── AI Providers
├── Social Connections
├── Tracking
├── Notifications
├── Audit Log
└── System
```

---

# 6. Core Modules

## 6.1 Product Management

### Product fields

- id
- sku
- slug
- name
- short_description
- description
- category_id
- base_price
- sale_price
- cost_price
- unit
- status
- featured
- tags
- ingredients
- allergens
- nutrition_text
- preparation_note
- storage_note
- shelf_life
- thumbnail
- media
- seo_title
- seo_description
- created_at
- updated_at

### Product status

```text
DRAFT
ACTIVE
OUT_OF_STOCK
HIDDEN
ARCHIVED
```

### Seed products

- Táo New Zealand giòn ngọt — 49.000đ
- Thanh long trắng/đỏ — 32.000đ
- Dưa lưới vàng — 49.000đ
- Nước ép thơm táo — 30.000đ
- Sinh tố bơ — 35.000đ
- Sữa chua dâu — 33.000đ
- Sữa chua xoài — 32.000đ
- Nước ép cam — 20.000đ
- Matcha latte — 35.000đ
- Trà dâu tây — giá thường 30.000đ / promo 25.000đ

### Acceptance criteria

- CRUD sản phẩm.
- Upload nhiều ảnh.
- Filter category / status / stock.
- Search theo name / SKU.
- Bulk enable / disable.
- Price validation.
- Sale price không lớn hơn base price.
- Audit thay đổi giá.

---

# 7. Inventory & Expiry

Trái cây / đồ uống có đặc thù hạn dùng ngắn, vì vậy inventory phải hỗ trợ theo batch.

## Entity

```text
InventoryBatch
- id
- product_id
- batch_code
- quantity_received
- quantity_available
- received_at
- expiry_at
- cost_per_unit
- supplier
- status
```

## Inventory movement

```text
PURCHASE_IN
SALE_OUT
WASTE_OUT
ADJUSTMENT_IN
ADJUSTMENT_OUT
RETURN_IN
```

## Alerts

- Stock <= minimum_stock.
- Sắp hết hạn.
- Tồn lâu.
- Waste tăng bất thường.

## FEFO

Ưu tiên xuất batch gần hết hạn trước:

```text
First Expired
First Out
```

---

# 8. Promotion Engine

Types:

```text
PERCENT_DISCOUNT
FIXED_DISCOUNT
FLASH_SALE
BUY_X_GET_Y
COMBO
FREE_SHIPPING
VOUCHER
```

Promotion fields:

- title
- code
- type
- value
- min_order_value
- max_discount
- start_at
- end_at
- product_scope
- customer_scope
- usage_limit
- usage_per_customer
- stackable
- status

Không hardcode promotion vào product.

---

# 9. Storefront / E-commerce

Public website:

```text
/
├── Trang chủ
├── Danh mục
├── Sản phẩm
├── Combo
├── Khuyến mãi
├── Search
├── Cart
├── Checkout
├── Order Tracking
├── Blog
└── Account
```

## Home sections

1. Hero.
2. Ưu đãi hôm nay.
3. Best sellers.
4. Trái cây cắt sẵn.
5. Nước ép / sinh tố.
6. Sữa chua.
7. Combo.
8. Reviews.
9. Blog / healthy tips.
10. CTA order.

## Cart

- Add / remove.
- Quantity.
- Promotion validation.
- Voucher.
- Estimated delivery.
- Cart tracking events.

## Checkout

- Guest checkout.
- Login checkout.
- Customer info.
- Address.
- Delivery note.
- Payment method.
- Promotion.
- Final total.

Payment adapter:

```text
COD
BANK_TRANSFER
ONLINE_PROVIDER_FUTURE
```

---

# 10. Order Management

## Order status

```text
NEW
CONFIRMED
PREPARING
READY
SHIPPING
COMPLETED
CANCELLED
REFUNDED
```

## Order entity

- order_number
- customer_id
- source
- subtotal
- discount
- shipping_fee
- total
- payment_status
- fulfillment_status
- customer_note
- internal_note
- created_at

## Order source

```text
WEBSITE
FACEBOOK
TIKTOK
ZALO
GRAB_MANUAL
WALK_IN
OTHER
```

---

# 11. Customer CRM

## Customer profile

- id
- full_name
- phone
- email
- date_of_birth optional
- default_address
- source
- first_order_at
- last_order_at
- order_count
- total_spent
- average_order_value
- loyalty_points
- tags
- consent flags

## Customer segments

MVP rule-based:

```text
NEW
ACTIVE
REPEAT
VIP
AT_RISK
DORMANT
HIGH_VALUE
PROMO_SENSITIVE
```

Later:
- RFM.
- Behavioral segmentation.
- AI clustering.

## Customer 360

Show:
- Profile.
- Orders.
- Total spend.
- Favorite products.
- Favorite category.
- Most used channel.
- Reviews.
- Marketing interaction.
- Automation history.

---

# 12. Campaign Management

## Campaign fields

- name
- objective
- status
- start_at
- end_at
- budget
- target_audience
- products
- channels
- promotion_id
- landing_page
- owner
- notes

## Objective

```text
AWARENESS
TRAFFIC
CONVERSION
REMARKETING
RETENTION
INVENTORY_CLEARANCE
NEW_PRODUCT
```

## Campaign status

```text
DRAFT
PLANNING
READY_FOR_REVIEW
APPROVED
ACTIVE
PAUSED
COMPLETED
CANCELLED
```

---

# 13. AI Marketing Strategist

Đầu vào:

```text
Sales
Inventory
Expiry
Customer
Campaign
Content Performance
Channel Performance
Promotions
```

Đầu ra bắt buộc dùng structured JSON.

## Recommendation schema

```json
{
  "title": "",
  "problem": "",
  "evidence": [],
  "recommended_action": "",
  "products": [],
  "customer_segment": "",
  "channels": [],
  "promotion": {},
  "suggested_schedule": [],
  "expected_metric": "",
  "confidence": 0,
  "risks": []
}
```

## AI use cases

- Hôm nay nên quảng bá sản phẩm nào?
- Sản phẩm nào cần flash sale?
- Campaign nào đang giảm hiệu quả?
- Channel nào nên ưu tiên?
- Khách hàng nào cần remarketing?
- Content nào nên tạo lại dưới format khác?
- Tại sao conversion giảm?

### Guardrails

AI:
- Không tự đặt giá cuối cùng nếu vượt rule.
- Không tự chi ngân sách nếu chưa approve.
- Không bịa tồn kho.
- Không bịa sales.
- Mọi recommendation phải liên kết evidence.
- Với dữ liệu không đủ phải trả về `insufficient_data=true`.

---

# 14. AI Content Studio

Input:

```text
Product
Campaign Goal
Target Customer
Promotion
Brand Tone
Channel
Desired Format
```

Output:

- Facebook caption.
- Instagram caption.
- TikTok hook.
- TikTok script.
- Reel script.
- Zalo message.
- Website banner copy.
- Product description.
- SEO article outline.
- CTA.
- Hashtag.
- Image generation brief.

## Content object

```text
ContentItem
- id
- campaign_id
- product_id
- type
- channel
- title
- body
- hook
- cta
- hashtags
- media_ids
- ai_generated
- ai_prompt_version
- status
- approved_by
- scheduled_at
- published_at
```

## Content status

```text
DRAFT
AI_GENERATED
IN_REVIEW
APPROVED
SCHEDULED
PUBLISHING
PUBLISHED
FAILED
ARCHIVED
```

---

# 15. Media Library

Folders / labels:

```text
PRODUCT
CAMPAIGN
SOCIAL
BANNER
VIDEO
AI_GENERATED
BRAND
TEMPLATE
```

Media metadata:

- alt text.
- dimensions.
- duration.
- mime type.
- tags.
- linked product.
- linked campaign.
- created_by.
- AI generated flag.

Storage:

```text
S3-compatible / MinIO
```

---

# 16. Content Calendar

Views:

- Day.
- Week.
- Month.
- Channel filter.
- Campaign filter.
- Product filter.
- Status filter.

Actions:

- Drag & drop schedule.
- Duplicate.
- Reschedule.
- Approve.
- Publish now.
- Cancel.
- Retry failed.

Calendar card shows:
- Thumbnail.
- Channel.
- Product.
- Campaign.
- Time.
- Status.

---

# 17. Multi-channel Publisher

Provider adapter interface:

```text
SocialProvider
├── validate_connection()
├── publish_text()
├── publish_image()
├── publish_video()
├── schedule_if_supported()
├── fetch_post_metrics()
└── refresh_token()
```

Providers:

```text
FacebookAdapter
InstagramAdapter
TikTokAdapter
ZaloAdapter
GoogleBusinessAdapter
WebsiteAdapter
```

Important:
- Một số nền tảng yêu cầu app approval / business verification.
- Trong development phải có `MockSocialProvider`.
- Không để business logic phụ thuộc trực tiếp SDK của platform.

## Publish flow

```text
APPROVED
  ↓
SCHEDULED
  ↓
QUEUE
  ↓
PUBLISHING
  ↓
PUBLISHED / FAILED
```

Retry:
- exponential backoff.
- max retry.
- dead-letter handling.
- error reason lưu DB.

---

# 18. Advertising Module

MVP:
- Lưu campaign ad metadata.
- Budget planned.
- Spend.
- Impressions.
- Clicks.
- Conversions.
- Revenue.
- ROAS.

Later:
- Meta Ads integration.
- TikTok Ads integration.
- Google Ads integration.
- AI budget recommendation.

Không cho AI auto-update budget trong MVP.

---


# 18A. Omnichannel Commerce Hub & External Marketplace Integration

Mộc Healthy phải được thiết kế theo nguyên tắc:

```text
Khách có thể mua ở nhiều nơi
→ Website / Grab / Zalo / POS / nền tảng khác
→ Mộc Platform là nơi hợp nhất dữ liệu kinh doanh
```

Mục tiêu không phải ép mọi khách hàng mua trên website. Website là **owned sales channel**, còn Mộc Platform là **central commerce & analytics hub**.

## 18A.1 Supported Sales Channels

```text
WEBSITE
GRAB
SHOPEEFOOD
ZALO
FACEBOOK
TIKTOK
POS
WALK_IN
OTHER
```

Không hardcode business logic riêng cho Grab ở nhiều nơi. Mọi external marketplace phải đi qua provider/adapter abstraction.

## 18A.2 Order Provider Abstraction

```text
OrderProvider
├── fetch_orders()
├── fetch_order_detail()
├── fetch_settlements()
├── fetch_promotions()
├── validate_connection()
└── normalize_order()
```

Implementations:

```text
WebsiteOrderProvider
GrabOrderProvider
ShopeeFoodOrderProvider
ManualImportOrderProvider
MockMarketplaceProvider
```

Nếu marketplace chưa có public API phù hợp hoặc chưa có credentials:
- hệ thống vẫn phải hỗ trợ import CSV/XLSX;
- giữ adapter interface;
- không fake API success.

## 18A.3 Unified Order Model

Mọi order sau khi normalize phải dùng cùng một data model.

Add/ensure fields:

```text
Order
- id
- internal_order_number
- channel
- external_order_id nullable
- external_store_id nullable
- customer_id nullable
- subtotal
- gross_amount
- merchant_discount
- platform_discount
- platform_fee
- shipping_fee
- other_fee
- net_amount
- payment_status
- fulfillment_status
- source
- medium
- campaign_id nullable
- content_id nullable
- external_campaign_ref nullable
- ordered_at
- settled_at nullable
- raw_import_id nullable
```

Unique rule:

```text
(channel, external_order_id)
```

phải idempotent khi `external_order_id` tồn tại.

## 18A.4 Revenue vs Settlement

Dashboard không được đồng nhất `gross sales` với `net income`.

Phải lưu riêng:

```text
Gross Sales / GMV
- Merchant Discount
- Platform Fee
- Shipping Subsidy/Cost
- Other Fees
= Net Settlement
```

Core metrics:

```text
gross_revenue
net_settlement
platform_fees
merchant_promotion_cost
order_count
average_order_value
net_revenue_per_order
```

Nếu dữ liệu cost sản phẩm đầy đủ có thể tính thêm gross profit.

## 18A.5 Marketplace Import

MVP phải hỗ trợ import report từ nền tảng ngoài:

```text
CSV / XLSX
→ Upload
→ Parse
→ Validate
→ Preview
→ Normalize
→ Detect duplicate
→ Import
→ Reconcile
```

Entity đề xuất:

```text
MarketplaceImport
- id
- provider
- filename
- status
- imported_rows
- rejected_rows
- duplicate_rows
- started_at
- completed_at
- error_report_path
```

Import phải:
- idempotent;
- có preview;
- không ghi một phần nếu transaction thất bại;
- có error report cho row lỗi.

## 18A.6 Settlement & Reconciliation

Entities:

```text
Settlement
- id
- provider
- external_settlement_id
- period_start
- period_end
- gross_amount
- platform_fee
- merchant_discount
- other_fee
- net_amount
- paid_at
- status

SettlementOrder
- settlement_id
- order_id
- allocated_amount
```

Reconciliation statuses:

```text
UNMATCHED
PARTIAL
MATCHED
DISPUTED
```

Dashboard phải cho phép đối chiếu:

```text
Orders
vs
Platform Report
vs
Settlement
```

## 18A.7 Smart Link / Tracking Redirect

Mọi quảng cáo dẫn sang external marketplace nên có thể đi qua Mộc Smart Link.

Example:

```text
https://go.mochealthy.vn/r/{slug}
```

Flow:

```text
Facebook / TikTok / Google
          ↓
      Smart Link
          ↓
 record click event
          ↓
   302/307 redirect
          ↓
 Website / Grab / Zalo / Other
```

Entity:

```text
SmartLink
- id
- slug
- destination_url
- channel
- product_id nullable
- campaign_id nullable
- content_id nullable
- active
- expires_at nullable

SmartLinkClick
- id
- smart_link_id
- click_id
- anonymous_id nullable
- timestamp
- source
- medium
- campaign
- content
- referrer
- user_agent_hash optional
```

Do not store unnecessary PII.

## 18A.8 External Conversion Attribution

Phải phân biệt rõ:

### Full attribution

```text
Ad
→ Mộc Website
→ Checkout
→ Purchase
```

Có thể map click/session/order chính xác.

### Partial / inferred attribution

```text
Ad
→ Smart Link
→ External Marketplace
→ Purchase
```

Nếu marketplace không trả conversion/order callback:
- chỉ chắc chắn biết outbound click;
- order attribution phải dựa trên promo code, campaign code, report mapping hoặc aggregate reconciliation;
- dashboard phải label là `INFERRED` hoặc `AGGREGATED`, không trình bày như deterministic attribution.

Attribution confidence:

```text
DETERMINISTIC
INFERRED
AGGREGATED
UNKNOWN
```

## 18A.9 Campaign / Promo Mapping

Cho phép mapping:

```text
Internal Campaign
↔ External Campaign Ref
↔ Promo Code
↔ Smart Link
↔ Channel
```

Ví dụ:

```text
Campaign: TIKTOK_OCT_DRINK01
Promo Code: MOC10TK
Destination: GRAB
Smart Link: /r/tiktok-dau-oct
```

Nhờ vậy analytics có thể tổng hợp revenue theo campaign ngay cả khi order diễn ra ngoài website.

## 18A.10 Omnichannel Dashboard

CEO dashboard phải có:

- Revenue by channel.
- Gross vs net.
- Platform fee by channel.
- Orders by channel.
- AOV by channel.
- Net revenue/order.
- Marketing spend by source.
- Smart-link outbound clicks.
- Deterministic vs inferred attributed revenue.
- Marketplace reconciliation status.

Example:

```text
Channel       Orders   Gross     Fees     Net
Website       210      18.2M     0.8M     17.4M
Grab          380      31.4M     8.1M     23.3M
Zalo           42       3.8M     0.1M      3.7M
Offline       160      12.6M       -      12.6M
```

## 18A.11 AI Usage

AI may analyze omnichannel data:

```text
"Grab tạo nhiều đơn hơn Website nhưng net revenue/order thấp hơn."
"TikTok tạo nhiều outbound click sang Grab."
"Website có AOV cao hơn external marketplace."
```

Rules:
- AI không được tự suy ra exact conversion nếu attribution chỉ là inferred.
- Insight phải hiển thị attribution confidence.
- AI phải tách gross revenue và net settlement.


# 19. Tracking & Event Taxonomy

Mọi event phải có:

- event_name
- anonymous_id
- user_id optional
- session_id
- timestamp
- page_url
- referrer
- utm_source
- utm_medium
- utm_campaign
- utm_content
- product_id optional
- order_id optional
- campaign_id optional
- metadata

## Core events

```text
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
order_completed
content_click
campaign_click
social_referral
customer_login
customer_signup
review_submitted
```

---

# 20. Attribution

MVP:
- First touch.
- Last touch.

Store:
- source.
- medium.
- campaign.
- content.
- landing page.

Later:
- assisted conversion.
- multi-touch attribution.

---

# 21. CEO Dashboard

## Top KPI

- Revenue.
- Orders.
- AOV.
- Conversion Rate.
- New Customers.
- Returning Customers.
- Repeat Purchase Rate.
- Marketing Spend.
- CAC.
- LTV.
- ROAS.
- Gross Profit if cost data available.

## Charts

- Revenue over time.
- Orders over time.
- Revenue by category.
- Revenue by product.
- Revenue by source.
- Funnel.
- Campaign performance.
- Channel performance.
- Customer segment.
- Inventory risk.

## AI Insight box

Example:

```text
Sữa chua dâu tăng 35% so với tuần trước.
TikTok đóng góp 42% đơn mới của sản phẩm này.
Đề xuất duy trì nội dung video vào khung giờ 18:00–21:00.
```

Mỗi insight phải:
- Có evidence.
- Có date range.
- Có action.
- Không dùng số liệu AI tự tưởng tượng.

---

# 22. Marketing Automation

## Workflow anatomy

```text
TRIGGER
  ↓
CONDITION
  ↓
ACTION
  ↓
WAIT
  ↓
CONDITION
  ↓
ACTION
```

## MVP workflows

### Welcome

```text
Customer Created
→ Has Consent?
→ Send Welcome Message
→ Wait
→ Offer first-order promotion
```

### Abandoned cart

```text
Add To Cart
→ No Purchase for X hours
→ Send reminder
→ Purchase?
→ Stop
```

### Repeat purchase

```text
Order Completed
→ Wait N days
→ Check category
→ Suggest related product
```

### Customer reactivation

```text
No purchase for X days
→ Customer segment AT_RISK
→ Create personalized offer
```

### Inventory clearance

```text
Batch nearing expiry
→ Quantity above threshold
→ Generate recommendation
→ Human approve
→ Create campaign
```

---

# 23. Alerts & Notifications

Alerts:

- Low stock.
- Expiry risk.
- High waste.
- Revenue anomaly.
- Conversion drop.
- ROAS drop.
- Publishing failed.
- Provider auth expired.
- Queue failure.
- AI provider error.
- Campaign ending soon.

Channels:

```text
IN_APP
EMAIL
TELEGRAM / SLACK FUTURE
```

---

# 24. Settings & RBAC

Core tables:

```text
users
roles
permissions
user_roles
role_permissions
```

Permission examples:

```text
product.read
product.write
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
```

---

# 25. Audit Log

Audit:

- Who.
- Action.
- Entity.
- Entity ID.
- Before.
- After.
- IP.
- User agent.
- Timestamp.

Bắt buộc audit:
- Price change.
- Promotion change.
- Campaign approval.
- Content approval.
- Manual publish.
- Role change.
- Provider connection change.

---

# 26. Recommended Technical Architecture

```text
                       INTERNET
                          │
                  Reverse Proxy / CDN
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Next.js Storefront       Next.js Admin
              │                       │
              └───────────┬───────────┘
                          ▼
                      FastAPI
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     PostgreSQL          Redis         Object Storage
                          │               MinIO/S3
                          ▼
                   Background Worker
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
         AI Provider   Social APIs   Notifications
```

## Stack

### Frontend

- Next.js.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.
- ECharts.
- Zustand only when local global state is justified.

### Backend

- FastAPI.
- Python.
- SQLAlchemy 2.
- Alembic.
- Pydantic.
- PostgreSQL.
- Redis.
- Celery or RQ for background jobs.

### Storage

- MinIO local/dev.
- S3-compatible production.

### Auth

- JWT access token.
- Refresh token.
- Password hashing.
- Role / permission middleware.

### AI

Provider abstraction:

```text
AIProvider
├── generate_text()
├── generate_json()
├── analyze()
└── generate_image_brief()
```

Có thể cấu hình nhiều provider.

### Observability

- Structured JSON logs.
- Request ID.
- Job ID.
- Error tracking.
- Health endpoint.
- Metrics endpoint later.

---

# 27. Suggested Monorepo Structure

```text
moc-healthy/
│
├── apps/
│   ├── admin-web/
│   ├── storefront-web/
│   └── api/
│
├── workers/
│   └── marketing-worker/
│
├── packages/
│   ├── ui/
│   ├── config/
│   └── contracts/
│
├── infra/
│   ├── docker/
│   ├── nginx/
│   └── scripts/
│
├── docs/
│   ├── PLAN.md
│   ├── API.md
│   ├── DATA_MODEL.md
│   ├── EVENT_TAXONOMY.md
│   └── ADR/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

Nếu muốn đơn giản hơn ở giai đoạn đầu có thể dùng 2 repo:

```text
moc-frontend
moc-backend
```

Nhưng monorepo giúp vibe coding giữ context tốt hơn.

---

# 28. Core Database Entities

```text
User
Role
Permission

Product
Category
ProductMedia

InventoryBatch
InventoryMovement

Promotion
Voucher

Customer
CustomerAddress
CustomerSegment
CustomerTag
LoyaltyTransaction

Cart
CartItem

Order
OrderItem
OrderStatusHistory
Payment

Campaign
CampaignChannel
CampaignProduct

ContentItem
ContentVersion
ContentApproval
ContentSchedule

MediaAsset

SocialConnection
PublishedPost
PostMetric

SmartLink
SmartLinkClick
MarketplaceImport
Settlement
SettlementOrder
IntegrationConnection

TrackingEvent
Session
Attribution

AutomationWorkflow
AutomationRun

AIRecommendation
AIInsight
AIGenerationLog

Notification
Alert

AuditLog
SystemSetting
```

---

# 29. API Design Principles

Base:

```text
/api/v1
```

Examples:

```text
GET    /products
POST   /products
GET    /products/{id}
PATCH  /products/{id}

GET    /inventory
POST   /inventory/batches
POST   /inventory/adjustments

GET    /orders
POST   /orders
PATCH  /orders/{id}/status

GET    /customers
GET    /customers/{id}
GET    /customers/{id}/timeline

GET    /campaigns
POST   /campaigns
POST   /campaigns/{id}/submit-review
POST   /campaigns/{id}/approve

POST   /ai/recommendations/generate
POST   /ai/content/generate
POST   /ai/campaign/generate

GET    /content
POST   /content/{id}/approve
POST   /content/{id}/schedule
POST   /content/{id}/publish

GET    /analytics/overview
GET    /analytics/revenue
GET    /analytics/campaigns

POST   /tracking/events
```

Rules:
- REST resource-based.
- Pagination.
- Filtering.
- Sorting.
- Standard error shape.
- Idempotency với order creation / publish job.
- OpenAPI docs.

---

# 30. Standard API Response

Success:

```json
{
  "data": {},
  "meta": {},
  "request_id": "..."
}
```

Error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "...",
    "details": {}
  },
  "request_id": "..."
}
```

---

# 31. UI Design System

Brand direction:
- Clean.
- Healthy.
- Natural.
- Fresh.
- Premium but friendly.

Primary:
- Deep green.

Background:
- White / soft gray.

Support:
- Light green.
- Amber for warnings.
- Red only for destructive / critical.

UI:
- Rounded cards.
- Clean table.
- Strong image usage.
- Desktop-first admin.
- Mobile-friendly storefront.

## Admin shell

```text
Sidebar
Topbar
Breadcrumb
Page Title
Global Search
Notifications
User Menu
```

## Required states

Mọi page phải có:
- loading
- empty
- error
- success
- permission denied
- skeleton
- mobile responsive where needed

---

# 32. Seed Data

Dùng data Mộc Healthy để demo:

```text
Táo New Zealand giòn ngọt   49,000
Thanh long trắng/đỏ         32,000
Dưa lưới vàng               49,000
Nước ép thơm táo            30,000
Sinh tố bơ                  35,000
Sữa chua dâu                33,000
Sữa chua xoài               32,000
Nước ép cam                 20,000
Matcha latte                35,000
Trà dâu tây                 30,000 → 25,000
```

Categories:
- Trái cây cắt sẵn.
- Nước ép.
- Sinh tố.
- Sữa chua.
- Matcha / Tea.
- Combo.

---

# 33. Security Baseline

- Hash password bằng modern password hash.
- Access + refresh token.
- Refresh token rotation.
- Rate limit auth.
- RBAC.
- CORS allow-list.
- Secure cookie nếu dùng cookie.
- Input validation.
- File upload validation.
- MIME whitelist.
- Max upload size.
- Signed URLs cho private asset nếu cần.
- Secrets chỉ ở environment / secret manager.
- Không log credentials.
- Không log access token.
- Audit admin actions.
- DB backup.
- CSRF protection nếu auth dựa cookie.
- SQL injection protection qua ORM / params.

---

# 34. Data Privacy

Customer fields:
- Chỉ thu thập thứ thực sự cần.
- Có consent cho marketing.
- Có unsubscribe.
- Có khả năng export / anonymize customer data khi cần.
- Không gửi dữ liệu customer không cần thiết vào AI provider.

AI payload:
- Prefer aggregate data.
- Mask phone/email.
- Không gửi raw PII khi không cần.

---

# 35. Testing Strategy

## Backend

- Unit tests.
- API integration tests.
- Permission tests.
- Promotion calculation tests.
- Inventory movement tests.
- Order total tests.
- AI structured output validation tests.

## Frontend

- Component tests.
- Form validation.
- Critical user flows.
- E2E bằng Playwright.

Critical E2E:

1. Admin login.
2. Create product.
3. Adjust stock.
4. Create promotion.
5. Customer add to cart.
6. Checkout.
7. Admin process order.
8. Create campaign.
9. Generate AI content.
10. Approve.
11. Schedule.
12. Mock publish.
13. Metrics appear dashboard.

---

# 36. CI/CD

Minimum pipeline:

```text
push / PR
   ↓
lint
   ↓
typecheck
   ↓
unit test
   ↓
integration test
   ↓
build
   ↓
docker build
```

Production:
- DB migration before app switch.
- Health check.
- Rollback procedure.
- Backup before breaking migration.

---

# 37. Environment Variables

Example:

```text
# DB
DATABASE_URL=

# Redis
REDIS_URL=

# JWT
JWT_SECRET=
JWT_REFRESH_SECRET=

# Storage
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=

# AI
AI_PROVIDER=
OPENAI_API_KEY=
GEMINI_API_KEY=

# Social
META_APP_ID=
META_APP_SECRET=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
ZALO_APP_ID=
ZALO_APP_SECRET=

# App
ADMIN_URL=
STOREFRONT_URL=
API_URL=
```

Never commit real secrets.

---

# 38. Feature Flags

Recommended:

```text
ENABLE_AI
ENABLE_SOCIAL_PUBLISHING
ENABLE_META
ENABLE_TIKTOK
ENABLE_ZALO
ENABLE_AUTOMATION
ENABLE_ADS_SYNC
ENABLE_ONLINE_PAYMENT
```

---

# 39. Delivery Roadmap

## Phase 0 — Foundation

- Repository.
- Docker.
- DB.
- Redis.
- Auth.
- RBAC.
- Design system.
- CI.
- Logging.
- Seed.

Exit:
- Developer có thể chạy toàn stack bằng 1 command.

---

## Phase 1 — Commerce Core

Build:
- Product.
- Category.
- Inventory.
- Promotion.
- Storefront.
- Cart.
- Checkout.
- Order.
- Customer.

Exit:
- Khách có thể đặt một đơn từ website.
- Admin xử lý được đơn tới completed.

---

## Phase 2 — CRM + Analytics Foundation

Build:
- Customer 360.
- Tracking events.
- UTM.
- Smart Link tracking.
- Attribution.
- External marketplace order import foundation.
- Basic dashboard.
- Revenue analytics.
- Gross vs net channel analytics.
- Funnel.

Exit:
- Biết đơn hàng đến từ nguồn nào.
- Có dashboard doanh thu và conversion.

---

## Phase 3 — Marketing Workspace

Build:
- Campaign.
- Content library.
- Calendar.
- Approval workflow.
- Social connections abstraction.
- Mock publisher.

Exit:
- Marketing có thể tạo campaign và content, approve, schedule.

---

## Phase 4 — AI Content

Build:
- AI provider abstraction.
- Content generation.
- Channel formatting.
- Prompt versioning.
- AI generation logs.
- Image brief.
- Video scripts.

Exit:
- Một product + campaign tạo được content pack đa kênh.

---

## Phase 5 — Real Social Publishing

Build provider adapters từng nền tảng theo khả năng API account:
- Meta.
- Instagram.
- TikTok.
- Zalo.
- Website.

Exit:
- Content approved có thể publish.
- Publish result / error được lưu.
- Retry hoạt động.

---

## Phase 6 — AI Analytics & Recommendation

Build:
- Product analysis.
- Campaign analysis.
- Channel analysis.
- Inventory risk.
- AI insight.
- Recommendation.

Exit:
- AI có thể trả recommendation có evidence, không bịa số liệu.

---

## Phase 7 — Automation

Build:
- Workflow engine.
- Trigger.
- Conditions.
- Actions.
- Wait.
- Automation run logs.

MVP automation:
- Welcome.
- Abandoned cart.
- Repeat purchase.
- Reactivation.
- Inventory clearance recommendation.

---

## Phase 8 — Ads & Optimization

Build:
- Ad spend import.
- Marketplace settlement import.
- Omnichannel reconciliation.
- Gross vs net channel analysis.
- ROAS.
- CAC.
- Campaign compare.
- Recommendation.

Later:
- Provider APIs.
- Budget suggestions.
- Human approval.

---

## Phase 9 — Production Hardening

- Performance.
- Security.
- Backup restore test.
- Error monitoring.
- Audit review.
- Permission review.
- Load test.
- UX polish.
- SEO.
- PWA optional.
- Runbook.

---

# 40. Definition of Done

Một feature chỉ được xem là DONE khi:

- Có UI.
- Có API.
- Có validation.
- Có permission.
- Có loading / empty / error state.
- Có test.
- Có audit nếu cần.
- Có docs.
- Không còn TypeScript / lint error.
- Migration reproducible.
- Seed/dev workflow không hỏng.
- Không hardcode secret.
- Happy path và failure path đều test.

---

# 41. Milestone Acceptance Tests

## Milestone A

```text
Admin tạo product
→ nhập stock
→ bật ACTIVE
→ storefront thấy product
```

## Milestone B

```text
Customer
→ xem product
→ add cart
→ checkout
→ tạo order
→ admin xác nhận
→ chuẩn bị
→ shipping
→ complete
```

## Milestone C

```text
Create campaign
→ select product
→ AI generate Facebook/TikTok/Instagram/Zalo
→ reviewer approve
→ schedule
→ mock publish
→ metrics sync
```

## Milestone D

```text
System detects stock/expiry issue
→ creates AI recommendation
→ CEO approves campaign
→ AI content pack
→ schedule
→ publish
→ conversion tracked
→ AI analyzes result
```

Milestone D là closed-loop marketing hoàn chỉnh.

## Milestone E — Omnichannel Revenue Hub

```text
TikTok Ad
→ Mộc Smart Link
→ Grab
→ Marketplace report imported
→ Order normalized
→ Settlement reconciled
→ Campaign/promo mapped
→ CEO dashboard shows gross/net revenue by channel
→ AI analysis clearly labels inferred attribution
```

Milestone E chứng minh Mộc Platform có thể quản lý thu nhập đa kênh, không chỉ đơn hàng website.


---

# 42. Initial Backlog Priority

## P0

- Auth.
- RBAC.
- Product.
- Category.
- Inventory.
- Storefront.
- Cart.
- Checkout.
- Order.
- Customer.
- Core dashboard.

## P1

- Promotion.
- Tracking.
- Campaign.
- Content.
- Calendar.
- AI Content.
- Mock Social Publisher.

## P2

- Real integrations.
- AI recommendation.
- Automation.
- Advanced attribution.
- Ads API.

---

# 43. What Not To Build Too Early

Không ưu tiên ở MVP:

- Microservices.
- Kubernetes.
- Complex ML model.
- Fully autonomous ad spending.
- Custom recommendation model.
- Complex loyalty levels.
- Multi-warehouse.
- Marketplace.
- Native mobile app.

Xây khi business chứng minh cần.

---

# 44. Vibe Coding Working Agreement

Mọi coding agent phải:

1. Đọc `PLAN.md`.
2. Kiểm tra code hiện tại trước khi tạo architecture mới.
3. Không rewrite module đang chạy nếu không cần.
4. Mỗi task phải nhỏ và testable.
5. Không dùng mock data ở production path.
6. Mock external provider phải tách khỏi real provider.
7. Không hardcode IDs / API keys.
8. Sau mỗi milestone:
   - lint
   - typecheck
   - tests
   - build
9. Update docs.
10. Ghi assumptions rõ nếu requirement chưa xác định.

---

# 45. Final Product State

Khi hệ thống hoàn thành:

```text
Owner mở Dashboard
      ↓
AI phát hiện:
"Dưa lưới tồn cao và tốc độ bán giảm"
      ↓
AI đề xuất:
"Flash Sale 15%, TikTok + Facebook"
      ↓
Owner chọn Create Campaign
      ↓
AI tạo:
- campaign
- captions
- video scripts
- website banner copy
- Zalo copy
      ↓
Marketing review
      ↓
Owner approve
      ↓
Scheduler publish
      ↓
Customer click
      ↓
Website checkout
      ↓
Order
      ↓
Revenue + attribution
      ↓
Analytics
      ↓
AI đánh giá campaign
      ↓
Recommendation tiếp theo
```

Đây là trạng thái đích của **Mộc Healthy AI Marketing & Commerce Platform**.
