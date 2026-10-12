/**
 * Mộc Healthy Platform - Shared Contracts & Types
 */

export type Role = 'ADMIN' | 'OWNER' | 'MARKETING' | 'SALES' | 'INVENTORY';

export type ProductStatus = 'DRAFT' | 'ACTIVE' | 'OUT_OF_STOCK' | 'HIDDEN' | 'ARCHIVED';

export type OrderStatus =
  | 'NEW'
  | 'CONFIRMED'
  | 'PREPARING'
  | 'READY'
  | 'SHIPPING'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'REFUNDED';

export type AttributionConfidence =
  | 'DETERMINISTIC'
  | 'INFERRED'
  | 'AGGREGATED'
  | 'UNKNOWN';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: Role[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ServiceHealth {
  database: 'connected' | 'disconnected' | 'mocked';
  redis: 'connected' | 'disconnected' | 'mocked';
  storage: 'connected' | 'disconnected' | 'mocked';
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down';
  environment: string;
  version: string;
  timestamp: string;
  services: ServiceHealth;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta?: {
    page?: number;
    pageSize?: number;
    total?: number;
    requestId?: string;
  };
}

// Commerce Core - Categories & Products Contracts

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  sort_order: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PriceAuditLog {
  id: string;
  product_id: string;
  old_base_price?: number | null;
  new_base_price: number;
  old_sale_price?: number | null;
  new_sale_price?: number | null;
  changed_by_user_id?: string | null;
  change_reason?: string | null;
  created_at: string;
}

export interface Product {
  id: string;
  sku: string;
  slug: string;
  name: string;
  short_description?: string | null;
  description?: string | null;
  category_id?: string | null;
  base_price: number;
  sale_price?: number | null;
  cost_price?: number | null;
  unit: string;
  status: ProductStatus;
  featured: boolean;
  tags: string[];
  ingredients?: string | null;
  allergens?: string | null;
  nutrition_text?: string | null;
  preparation_note?: string | null;
  storage_note?: string | null;
  shelf_life?: string | null;
  thumbnail?: string | null;
  media: string[];
  low_stock_threshold?: number;
  seo_title?: string | null;
  seo_description?: string | null;
  created_at: string;
  updated_at: string;
  category?: Category | null;
}

export interface ProductDetail extends Product {
  price_logs: PriceAuditLog[];
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BulkStatusUpdateRequest {
  ids: string[];
  status: ProductStatus;
}

// Media Contracts

export interface MediaAsset {
  id: string;
  filename: string;
  original_name: string;
  mime_type: string;
  file_size: number;
  url: string;
  thumbnail_url?: string | null;
  width?: number | null;
  height?: number | null;
  tags: string[];
  folder: string;
  created_at: string;
}

export interface MediaAssetListResponse {
  items: MediaAsset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Inventory & Expiry Contracts

export type InventoryBatchStatus =
  | 'ACTIVE'
  | 'DEPLETED'
  | 'EXPIRED'
  | 'QUARANTINED'
  | 'DISCARDED';

export type InventoryMovementType =
  | 'PURCHASE_IN'
  | 'SALE_OUT'
  | 'WASTE_OUT'
  | 'ADJUSTMENT_IN'
  | 'ADJUSTMENT_OUT'
  | 'RETURN_IN';

export interface InventoryBatch {
  id: string;
  product_id: string;
  batch_code: string;
  quantity_received: number;
  quantity_available: number;
  cost_per_unit?: number | null;
  supplier?: string | null;
  received_at: string;
  expiry_at: string;
  status: InventoryBatchStatus;
  note?: string | null;
  created_at: string;
  updated_at: string;
  product_name?: string | null;
  product_sku?: string | null;
  product_unit?: string | null;
  days_to_expiry?: number | null;
  hours_to_expiry?: number | null;
  is_expired: boolean;
  is_critical: boolean;
  is_warning: boolean;
}

export interface InventoryMovement {
  id: string;
  batch_id: string;
  product_id: string;
  movement_type: InventoryMovementType;
  quantity: number;
  previous_quantity: number;
  new_quantity: number;
  reference_id?: string | null;
  reason?: string | null;
  note?: string | null;
  created_by_user_id?: string | null;
  created_at: string;
  batch_code?: string | null;
  product_name?: string | null;
  created_by_user_name?: string | null;
}

export interface ProductInventorySummary {
  product_id: string;
  product_name: string;
  sku: string;
  unit: string;
  base_price: number;
  sale_price?: number | null;
  cost_price?: number | null;
  low_stock_threshold: number;
  total_available: number;
  batch_count: number;
  nearest_expiry?: string | null;
  is_low_stock: boolean;
  has_expiring_batches: boolean;
  has_expired_batches: boolean;
}

export interface InventoryOverview {
  total_products: number;
  total_batches: number;
  total_stock_units: number;
  low_stock_products_count: number;
  expiring_soon_batches_count: number;
  critical_batches_count: number;
  expired_batches_count: number;
  total_inventory_value: number;
}

export interface ExpiryAlertItem {
  batch_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  batch_code: string;
  quantity_available: number;
  expiry_at: string;
  days_to_expiry: number;
  hours_to_expiry: number;
  urgency: 'EXPIRED' | 'CRITICAL' | 'WARNING' | 'ATTENTION';
  estimated_waste_cost: number;
}

export interface FefoAllocationItem {
  batch_id: string;
  batch_code: string;
  allocated_quantity: number;
  quantity_before: number;
  quantity_after: number;
  expiry_at: string;
}

export interface FefoAllocationResult {
  product_id: string;
  product_name: string;
  requested_quantity: number;
  allocated_quantity: number;
  is_fully_allocated: boolean;
  allocations: FefoAllocationItem[];
}

// Promotion & Voucher Contracts

export type PromotionType =
  | 'PERCENT_DISCOUNT'
  | 'FIXED_DISCOUNT'
  | 'FLASH_SALE'
  | 'BUY_X_GET_Y'
  | 'COMBO'
  | 'FREE_SHIPPING'
  | 'VOUCHER';

export type PromotionStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'PAUSED'
  | 'EXPIRED'
  | 'ARCHIVED';

export type ProductScope =
  | 'ALL'
  | 'SPECIFIC_PRODUCTS'
  | 'SPECIFIC_CATEGORIES';

export type CustomerScope =
  | 'ALL'
  | 'NEW_CUSTOMER'
  | 'VIP';

export interface Promotion {
  id: string;
  title: string;
  code?: string | null;
  description?: string | null;
  type: PromotionType;
  value: number;
  min_order_value?: number | null;
  max_discount?: number | null;
  start_at: string;
  end_at: string;
  product_scope: ProductScope;
  applicable_product_ids: string[];
  applicable_category_ids: string[];
  buy_x_get_y_config?: Record<string, any> | null;
  combo_config?: Record<string, any> | null;
  customer_scope: CustomerScope;
  usage_limit?: number | null;
  usage_count: number;
  usage_per_customer?: number | null;
  stackable: boolean;
  status: PromotionStatus;
  created_at: string;
  updated_at: string;
  is_valid_now?: boolean;
}

export interface PromotionCreateInput {
  title: string;
  code?: string | null;
  description?: string | null;
  type: PromotionType;
  value: number;
  min_order_value?: number | null;
  max_discount?: number | null;
  start_at: string;
  end_at: string;
  product_scope: ProductScope;
  applicable_product_ids?: string[];
  applicable_category_ids?: string[];
  buy_x_get_y_config?: Record<string, any> | null;
  combo_config?: Record<string, any> | null;
  customer_scope?: CustomerScope;
  usage_limit?: number | null;
  usage_per_customer?: number | null;
  stackable?: boolean;
  status?: PromotionStatus;
}

export interface PromotionUpdateInput extends Partial<PromotionCreateInput> {}

export interface PromotionListResponse {
  items: Promotion[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CartItemCalculationInput {
  product_id: string;
  quantity: number;
  unit_price: number;
  category_id?: string | null;
  name?: string | null;
}

export interface PromotionCalculationInput {
  items: CartItemCalculationInput[];
  promo_code?: string | null;
  shipping_fee?: number;
  is_new_customer?: boolean;
  as_of?: string | null;
}

export interface AppliedPromotionItem {
  promotion_id: string;
  title: string;
  code?: string | null;
  type: PromotionType;
  discount_amount: number;
  description: string;
}

export interface FreeGiftItem {
  product_id: string;
  product_name: string;
  quantity: number;
  reason: string;
}

export interface PromotionCalculationResult {
  subtotal: number;
  discount_amount: number;
  shipping_fee: number;
  shipping_discount: number;
  final_total: number;
  applied_promotions: AppliedPromotionItem[];
  free_items: FreeGiftItem[];
  rejection_reasons: string[];
  is_code_valid: boolean;
}

// Storefront (Public E-commerce) Contracts

export interface StorefrontCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  sort_order: number;
  product_count: number;
}

export interface StorefrontProduct {
  id: string;
  sku: string;
  slug: string;
  name: string;
  short_description?: string | null;
  description?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  category_slug?: string | null;
  base_price: number;
  sale_price?: number | null;
  discount_percent?: number | null;
  unit: string;
  status: string;
  featured: boolean;
  tags: string[];
  ingredients?: string | null;
  allergens?: string | null;
  nutrition_text?: string | null;
  preparation_note?: string | null;
  storage_note?: string | null;
  shelf_life?: string | null;
  thumbnail?: string | null;
  media: string[];
}

export interface StorefrontProductDetail extends StorefrontProduct {
  related_products: StorefrontProduct[];
}

export interface StorefrontPromotionItem {
  id: string;
  title: string;
  code?: string | null;
  description?: string | null;
  type: string;
  value: number;
  min_order_value?: number | null;
  max_discount?: number | null;
  start_at: string;
  end_at: string;
  stackable: boolean;
}

export interface StorefrontHomeResponse {
  banners: StorefrontPromotionItem[];
  categories: StorefrontCategory[];
  featured_products: StorefrontProduct[];
  category_sections: Record<string, StorefrontProduct[]>;
  active_vouchers: StorefrontPromotionItem[];
}

export interface StorefrontProductListResponse {
  items: StorefrontProduct[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Cart & Checkout Contracts

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  product_slug: string;
  product_unit: string;
  thumbnail?: string | null;
  unit_price: number;
  original_price: number;
  quantity: number;
  line_total: number;
  note?: string | null;
  is_available: boolean;
  stock_available: number;
}

export interface CartResponse {
  cart_token: string;
  items: CartItem[];
  total_items: number;
  subtotal: number;
  discount_amount: number;
  shipping_fee: number;
  shipping_discount: number;
  final_total: number;
  applied_promo_code?: string | null;
  applied_promo_title?: string | null;
  promo_message?: string | null;
  free_gifts: FreeGiftItem[];
  warnings: string[];
}

export interface AddToCartInput {
  product_id: string;
  quantity?: number;
  note?: string | null;
}

export interface UpdateCartItemInput {
  quantity: number;
  note?: string | null;
}

export type PaymentMethod = 'COD' | 'BANK_TRANSFER';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED';

export interface BankTransferInstruction {
  bank_name: string;
  bank_code: string;
  account_number: string;
  account_holder: string;
  transfer_content: string;
  amount: number;
  qr_code_url: string;
}

export interface OrderItemSnapshot {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  product_unit: string;
  thumbnail?: string | null;
  unit_price: number;
  quantity: number;
  total_price: number;
  note?: string | null;
}

export interface CheckoutInput {
  cart_token: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string | null;
  delivery_address: string;
  customer_note?: string | null;
  payment_method: PaymentMethod;
  terms_accepted: boolean;
  idempotency_key?: string | null;
}

export interface CheckoutResult {
  order_id: string;
  order_number: string;
  status: OrderStatus;
  customer_name: string;
  customer_phone: string;
  customer_email?: string | null;
  delivery_address: string;
  customer_note?: string | null;
  items: OrderItemSnapshot[];
  subtotal: number;
  discount_amount: number;
  shipping_fee: number;
  shipping_discount: number;
  total_amount: number;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  applied_promo_code?: string | null;
  bank_transfer_instruction?: BankTransferInstruction | null;
  created_at: string;
}

export interface CartValidationIssue {
  product_id: string;
  product_name: string;
  issue_type: string;
  message: string;
}

export interface CartValidationResult {
  is_valid: boolean;
  issues: CartValidationIssue[];
  cart: CartResponse;
}

// Order Management Contracts (Prompt 11)

export type OrderSource = 'ONLINE' | 'PHONE' | 'WALK_IN' | 'ZALO' | 'FACEBOOK';

export interface OrderStatusHistoryItem {
  id: string;
  order_id: string;
  old_status?: OrderStatus | null;
  new_status: OrderStatus;
  changed_by_user_id?: string | null;
  reason?: string | null;
  created_at: string;
}

export interface AdminOrderListItem {
  id: string;
  order_number: string;
  status: OrderStatus;
  source: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string | null;
  delivery_address: string;
  items_count: number;
  subtotal: number;
  discount_amount: number;
  shipping_fee: number;
  total_amount: number;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  customer_note?: string | null;
  internal_note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminOrderDetail extends AdminOrderListItem {
  shipping_discount: number;
  applied_promo_code?: string | null;
  items: OrderItemSnapshot[];
  status_history: OrderStatusHistoryItem[];
}

export interface AdminOrderListResponse {
  items: AdminOrderListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OrderOverviewStats {
  total_orders: number;
  new_orders: number;
  in_progress_orders: number;
  completed_today: number;
  cancelled_today: number;
  revenue_today: number;
}

export interface OrderStatusUpdateRequest {
  new_status: OrderStatus;
  reason?: string | null;
}

export interface OrderPaymentStatusUpdateRequest {
  payment_status: PaymentStatus;
  note?: string | null;
}

export interface OrderInternalNoteUpdateRequest {
  internal_note?: string | null;
}

export interface ManualOrderCreateItem {
  product_id: string;
  quantity: number;
  note?: string | null;
}

export interface ManualOrderCreateRequest {
  customer_name: string;
  customer_phone: string;
  customer_email?: string | null;
  delivery_address: string;
  customer_note?: string | null;
  internal_note?: string | null;
  source: string;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  shipping_fee?: number;
  promo_code?: string | null;
  items: ManualOrderCreateItem[];
}

export interface OrderTrackingRequest {
  order_number: string;
  phone?: string | null;
}

export interface OrderTrackingResponse {
  order_number: string;
  status: OrderStatus;
  created_at: string;
  customer_name: string;
  delivery_address: string;
  total_amount: number;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  items: OrderItemSnapshot[];
  status_history: OrderStatusHistoryItem[];
}

// PROMPT 11A: Omnichannel Order Hub & Marketplace Import Contracts

export type MarketplaceChannel =
  | 'WEBSITE'
  | 'GRAB'
  | 'SHOPEEFOOD'
  | 'ZALO'
  | 'FACEBOOK'
  | 'TIKTOK'
  | 'POS'
  | 'MANUAL';

export interface MarketplaceImportPreviewItem {
  row_index: number;
  external_order_id: string;
  channel: string;
  customer_name: string;
  customer_phone: string;
  ordered_at: string;
  gross_amount: number;
  merchant_discount: number;
  platform_fee: number;
  net_amount: number;
  items_count: number;
  is_duplicate: boolean;
  error?: string | null;
}

export interface MarketplaceImportPreviewResponse {
  channel: string;
  filename: string;
  total_rows: number;
  valid_rows: number;
  duplicate_rows: number;
  error_rows: number;
  gross_amount_total: number;
  platform_fee_total: number;
  merchant_discount_total: number;
  net_settlement_total: number;
  preview_items: MarketplaceImportPreviewItem[];
}

export interface MarketplaceImportExecuteRequest {
  channel: string;
  filename: string;
  raw_content: string;
  skip_duplicates?: boolean;
}

export interface MarketplaceImportResponse {
  id: string;
  channel: string;
  filename: string;
  file_format: string;
  status: string;
  total_rows: number;
  imported_rows: number;
  duplicate_rows: number;
  rejected_rows: number;
  gross_amount_total: number;
  platform_fee_total: number;
  merchant_discount_total: number;
  net_settlement_total: number;
  started_at: string;
  completed_at?: string | null;
}

export interface SettlementCreateRequest {
  channel: string;
  external_settlement_id?: string | null;
  period_start: string;
  period_end: string;
  gross_amount: number;
  platform_fee: number;
  merchant_discount?: number;
  other_fee?: number;
  notes?: string | null;
}

export interface SettlementResponse {
  id: string;
  channel: string;
  external_settlement_id?: string | null;
  period_start: string;
  period_end: string;
  gross_amount: number;
  platform_fee: number;
  merchant_discount: number;
  other_fee: number;
  net_amount: number;
  status: 'UNMATCHED' | 'PARTIAL' | 'MATCHED' | 'DISPUTED';
  paid_at?: string | null;
  notes?: string | null;
  matched_orders_count: number;
  matched_amount: number;
  discrepancy_amount: number;
  created_at: string;
}

export interface SettlementReconcileResult {
  settlement_id: string;
  status: string;
  total_orders_in_period: number;
  matched_orders: number;
  unmatched_orders: number;
  total_settlement_net: number;
  total_orders_net: number;
  discrepancy: number;
}

export interface ChannelPnLSummary {
  channel: string;
  order_count: number;
  gross_revenue: number;
  merchant_discount: number;
  platform_fees: number;
  net_settlement: number;
  average_order_value: number;
  net_revenue_per_order: number;
  net_margin_percentage: number;
}

export interface OmnichannelPnLResponse {
  period_start?: string | null;
  period_end?: string | null;
  channels: ChannelPnLSummary[];
  totals: ChannelPnLSummary;
}

// PROMPT 12: Customer CRM & Loyalty Hub Contracts

export type CustomerSegment =
  | 'NEW'
  | 'ACTIVE'
  | 'REPEAT'
  | 'VIP'
  | 'AT_RISK'
  | 'DORMANT'
  | 'HIGH_VALUE'
  | 'PROMO_SENSITIVE';

export type LoyaltyTransactionType = 'EARN' | 'REDEEM' | 'ADJUSTMENT' | 'EXPIRE';

export interface CustomerListItem {
  id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  default_address?: string | null;
  source: string;
  segment: CustomerSegment;
  order_count: number;
  total_spent: number;
  average_order_value: number;
  loyalty_points: number;
  tags: string[];
  last_order_at?: string | null;
  created_at: string;
}

export interface CustomerListResponse {
  items: CustomerListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CustomerCreateInput {
  full_name: string;
  phone: string;
  email?: string | null;
  date_of_birth?: string | null;
  default_address?: string | null;
  source?: string;
  tags?: string[];
  notes?: string | null;
  consent_marketing?: boolean;
}

export interface CustomerUpdateInput {
  full_name?: string;
  email?: string | null;
  date_of_birth?: string | null;
  default_address?: string | null;
  tags?: string[];
  notes?: string | null;
  consent_marketing?: boolean;
  segment?: CustomerSegment;
}

export interface LoyaltyTransactionItem {
  id: string;
  customer_id: string;
  order_id?: string | null;
  transaction_type: LoyaltyTransactionType;
  points: number;
  balance_after: number;
  reason: string;
  created_by_user_id?: string | null;
  created_at: string;
}

export interface LoyaltyAdjustRequest {
  points: number;
  reason: string;
}

export interface CustomerOrderSummary {
  id: string;
  order_number: string;
  status: string;
  payment_status: string;
  total_amount: number;
  items_count: number;
  source: string;
  created_at: string;
}

export interface FavoriteProductItem {
  product_name: string;
  quantity_bought: number;
  total_spent: number;
}

export interface Customer360Response {
  id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  date_of_birth?: string | null;
  default_address?: string | null;
  source: string;
  segment: CustomerSegment;
  order_count: number;
  total_spent: number;
  average_order_value: number;
  loyalty_points: number;
  tags: string[];
  notes?: string | null;
  consent_marketing: boolean;
  first_order_at?: string | null;
  last_order_at?: string | null;
  days_since_last_order?: number | null;
  most_used_channel: string;
  favorite_products: FavoriteProductItem[];
  recent_orders: CustomerOrderSummary[];
  recent_loyalty_transactions: LoyaltyTransactionItem[];
  created_at: string;
}

export interface CustomerOverviewStats {
  total_customers: number;
  vip_customers: number;
  new_customers_this_month: number;
  at_risk_customers: number;
  total_loyalty_points_circulating: number;
  average_ltv: number;
}

// -------------------------------------------------------------
// Marketing Campaign Types (PLAN.md Section 12)
// -------------------------------------------------------------

export type CampaignObjective =
  | 'CONVERSION'
  | 'AWARENESS'
  | 'CLEARANCE'
  | 'REENGAGEMENT'
  | 'LOYALTY';

export type CampaignStatus =
  | 'DRAFT'
  | 'PLANNING'
  | 'READY_FOR_REVIEW'
  | 'APPROVED'
  | 'ACTIVE'
  | 'PAUSED'
  | 'COMPLETED'
  | 'CANCELLED';

export type MarketingChannel =
  | 'FACEBOOK'
  | 'ZALO'
  | 'TIKTOK'
  | 'INSTAGRAM'
  | 'SMS'
  | 'EMAIL'
  | 'WEBSITE_BANNER';

export interface CampaignChannelItem {
  id: string;
  campaign_id: string;
  channel: MarketingChannel | string;
  channel_budget: number;
  channel_spend: number;
  status: string;
  target_metric?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface CampaignProductItem {
  id: string;
  campaign_id: string;
  product_id: string;
  product_name: string;
  product_price: number;
  is_hero_product: boolean;
  special_price?: number | null;
  created_at: string;
}

export interface CampaignListItem {
  id: string;
  name: string;
  code: string;
  objective: CampaignObjective | string;
  status: CampaignStatus | string;
  start_at: string;
  end_at: string;
  budget: number;
  actual_spend: number;
  revenue_attributed: number;
  roi_percentage: number;
  target_audience: string[];
  channels_count: number;
  products_count: number;
  created_at: string;
}

export interface CampaignDetailResponse {
  id: string;
  name: string;
  code: string;
  objective: CampaignObjective | string;
  status: CampaignStatus | string;
  start_at: string;
  end_at: string;
  budget: number;
  actual_spend: number;
  revenue_attributed: number;
  roi_percentage: number;
  target_audience: string[];
  promotion_id?: string | null;
  promotion_name?: string | null;
  landing_page?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  notes?: string | null;
  created_by_user_id?: string | null;
  created_by_user_name?: string | null;
  approved_by_user_id?: string | null;
  approved_by_user_name?: string | null;
  approved_at?: string | null;
  channels: CampaignChannelItem[];
  products: CampaignProductItem[];
  created_at: string;
  updated_at: string;
}

export interface CampaignListResponse {
  items: CampaignListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CampaignOverviewStats {
  active_campaigns: number;
  ready_for_review_campaigns: number;
  total_budget_approved: number;
  total_revenue_attributed: number;
  average_roi_percentage: number;
}

export interface CampaignCreateInput {
  name: string;
  code: string;
  objective?: CampaignObjective | string;
  start_at: string;
  end_at: string;
  budget?: number;
  target_audience?: string[];
  promotion_id?: string | null;
  landing_page?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  notes?: string | null;
  channels?: Array<{
    channel: MarketingChannel | string;
    channel_budget?: number;
    target_metric?: string | null;
    notes?: string | null;
  }>;
  products?: Array<{
    product_id: string;
    is_hero_product?: boolean;
    special_price?: number | null;
  }>;
}

export interface CampaignUpdateInput {
  name?: string;
  objective?: CampaignObjective | string;
  start_at?: string;
  end_at?: string;
  budget?: number;
  target_audience?: string[];
  promotion_id?: string | null;
  landing_page?: string | null;
  notes?: string | null;
  channels?: Array<{
    channel: MarketingChannel | string;
    channel_budget?: number;
    target_metric?: string | null;
    notes?: string | null;
  }>;
  products?: Array<{
    product_id: string;
    is_hero_product?: boolean;
    special_price?: number | null;
  }>;
}

// -------------------------------------------------------------
// AI Content Studio & Social Publisher Types (PLAN.md Section 14, 16, 17)
// -------------------------------------------------------------

export type ContentType =
  | 'FACEBOOK_POST'
  | 'INSTAGRAM_POST'
  | 'TIKTOK_SCRIPT'
  | 'REEL_SCRIPT'
  | 'ZALO_MESSAGE'
  | 'WEBSITE_BANNER_COPY'
  | 'PRODUCT_STORY'
  | 'SEO_ARTICLE';

export type ContentChannel =
  | 'FACEBOOK'
  | 'INSTAGRAM'
  | 'TIKTOK'
  | 'ZALO'
  | 'SMS'
  | 'EMAIL'
  | 'WEBSITE_BANNER';

export type ContentStatus =
  | 'DRAFT'
  | 'AI_GENERATED'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'SCHEDULED'
  | 'PUBLISHING'
  | 'PUBLISHED'
  | 'FAILED'
  | 'ARCHIVED';

export type BrandTone =
  | 'FRESH_ENERGETIC'
  | 'NUTRITION_EXPERT'
  | 'WARM_FRIENDLY'
  | 'MINIMAL_HEALTHY'
  | 'TRENDY_HUMOR';

export interface ContentListItem {
  id: string;
  title: string;
  content_type: ContentType | string;
  channel: ContentChannel | string;
  status: ContentStatus | string;
  brand_tone: BrandTone | string;
  hook?: string | null;
  body_snippet: string;
  cta?: string | null;
  hashtags: string[];
  media_asset_ids: string[];
  campaign_id?: string | null;
  campaign_name?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  ai_generated: boolean;
  ai_model?: string | null;
  scheduled_at?: string | null;
  published_at?: string | null;
  external_post_url?: string | null;
  created_at: string;
}

export interface ContentListResponse {
  items: ContentListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ContentDetailResponse {
  id: string;
  title: string;
  content_type: ContentType | string;
  channel: ContentChannel | string;
  status: ContentStatus | string;
  brand_tone: BrandTone | string;
  hook?: string | null;
  body: string;
  cta?: string | null;
  hashtags: string[];
  media_asset_ids: string[];
  campaign_id?: string | null;
  campaign_name?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  product_price?: number | null;
  ai_generated: boolean;
  ai_model?: string | null;
  ai_prompt?: string | null;
  scheduled_at?: string | null;
  published_at?: string | null;
  external_post_id?: string | null;
  external_post_url?: string | null;
  error_message?: string | null;
  retry_count: number;
  metrics: Record<string, any>;
  created_by_user_id?: string | null;
  created_by_user_name?: string | null;
  approved_by_user_id?: string | null;
  approved_by_user_name?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentCalendarItem {
  id: string;
  title: string;
  content_type: ContentType | string;
  channel: ContentChannel | string;
  status: ContentStatus | string;
  scheduled_at?: string | null;
  published_at?: string | null;
  campaign_name?: string | null;
  product_name?: string | null;
}

export interface ContentOverviewStats {
  total_items: number;
  published_items: number;
  scheduled_items: number;
  in_review_items: number;
  draft_items: number;
  ai_generated_items: number;
}

export interface ContentCreateInput {
  title: string;
  content_type?: ContentType | string;
  channel?: ContentChannel | string;
  brand_tone?: BrandTone | string;
  hook?: string | null;
  body: string;
  cta?: string | null;
  hashtags?: string[];
  media_asset_ids?: string[];
  campaign_id?: string | null;
  product_id?: string | null;
  scheduled_at?: string | null;
}

export interface ContentUpdateInput {
  title?: string;
  content_type?: ContentType | string;
  channel?: ContentChannel | string;
  brand_tone?: BrandTone | string;
  hook?: string | null;
  body?: string;
  cta?: string | null;
  hashtags?: string[];
  media_asset_ids?: string[];
  campaign_id?: string | null;
  product_id?: string | null;
  scheduled_at?: string | null;
}

export interface AIGeneratedVariant {
  title: string;
  hook: string;
  body: string;
  cta: string;
  hashtags: string[];
  storyboard_suggestion?: string | null;
  rationale: string;
}

export interface AIGenerateRequest {
  product_id?: string | null;
  campaign_id?: string | null;
  channel?: ContentChannel | string;
  content_type?: ContentType | string;
  brand_tone?: BrandTone | string;
  custom_instruction?: string | null;
  num_variants?: number;
}

export interface AIGenerateResponse {
  variants: AIGeneratedVariant[];
  prompt_used: string;
  model_name: string;
  product_name?: string | null;
  campaign_name?: string | null;
}

// Marketing Analytics & Attribution Engine (Prompt 15)

export type AttributionModelType = 'FIRST_TOUCH' | 'LAST_TOUCH' | 'LINEAR' | 'TIME_DECAY';
export type AttributionConfidenceType = 'DETERMINISTIC' | 'INFERRED' | 'AGGREGATED' | 'UNKNOWN';

export interface TrackingEventInput {
  event_name: string;
  anonymous_id: string;
  session_id: string;
  user_id?: string | null;
  customer_id?: string | null;
  page_url?: string | null;
  referrer?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  utm_content?: string | null;
  utm_term?: string | null;
  channel?: string | null;
  product_id?: string | null;
  order_id?: string | null;
  campaign_id?: string | null;
  content_id?: string | null;
  event_metadata?: Record<string, any>;
}

export interface ConversionAttributionItem {
  id: string;
  order_id: string;
  order_number: string;
  attribution_model: AttributionModelType | string;
  confidence: AttributionConfidenceType | string;
  first_touch_source?: string | null;
  last_touch_source?: string | null;
  campaign_id?: string | null;
  campaign_code?: string | null;
  content_id?: string | null;
  touchpoints_count: number;
  order_revenue: number;
  attributed_revenue: number;
  attribution_weight: number;
  touchpoint_details: Array<Record<string, any>>;
  created_at: string;
}

export interface AnalyticsKPIOverview {
  gross_revenue: number;
  net_revenue: number;
  total_orders: number;
  aov: number;
  attributed_revenue: number;
  attribution_rate: number;
  marketing_spend: number;
  roas: number;
  mer: number;
  new_customers: number;
  returning_customers: number;
  cac: number;
  ltv: number;
  ltv_to_cac_ratio: number;
}

export interface ChannelAnalyticsItem {
  channel: string;
  channel_name: string;
  orders_count: number;
  gross_sales: number;
  platform_fees: number;
  merchant_discounts: number;
  net_revenue: number;
  net_margin_percentage: number;
  aov: number;
  share_of_sales: number;
}

export interface CampaignAttributionComparison {
  campaign_id: string;
  campaign_name: string;
  campaign_code: string;
  channel: string;
  spend: number;
  first_touch_revenue: number;
  first_touch_roas: number;
  last_touch_revenue: number;
  last_touch_roas: number;
  linear_revenue: number;
  linear_roas: number;
  confidence: AttributionConfidenceType | string;
  orders_count: number;
  new_customers_acquired: number;
}

export interface FunnelStepItem {
  step_key: string;
  step_name: string;
  count: number;
  conversion_from_top: number;
  drop_off_rate: number;
}

export interface AIAnalyticsInsightItem {
  type: 'SUCCESS' | 'WARNING' | 'RECOMMENDATION' | 'INFO' | string;
  title: string;
  description: string;
  metric_highlight?: string | null;
  suggested_action?: string | null;
}

export interface AnalyticsDashboardResponse {
  period: string;
  start_date: string;
  end_date: string;
  kpis: AnalyticsKPIOverview;
  channel_breakdown: ChannelAnalyticsItem[];
  campaign_attributions: CampaignAttributionComparison[];
  funnel: FunnelStepItem[];
  ai_insights: AIAnalyticsInsightItem[];
}

// -------------------------------------------------------------
// Marketing Automation & Customer Journeys Contracts
// -------------------------------------------------------------

export type TriggerType =
  | 'CUSTOMER_CREATED'
  | 'CART_ABANDONED'
  | 'ORDER_COMPLETED'
  | 'CUSTOMER_INACTIVE'
  | 'INVENTORY_EXPIRY_RISK'
  | 'LOW_STOCK'
  | 'CAMPAIGN_ENDING';

export type WorkflowStatus = 'ACTIVE' | 'PAUSED' | 'DRAFT' | 'ARCHIVED';

export type RunStatus = 'RUNNING' | 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED' | 'CANCELLED';

export type ActionType =
  | 'SEND_ZALO_MOCK'
  | 'SEND_EMAIL_MOCK'
  | 'ISSUE_PROMOTION'
  | 'ADD_LOYALTY_POINTS'
  | 'ADD_CUSTOMER_TAG'
  | 'CREATE_NOTIFICATION'
  | 'CREATE_RECOMMENDATION'
  | 'CREATE_CAMPAIGN_DRAFT'
  | 'WAIT_HOURS';

export interface ConditionItem {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'contains' | 'is_true' | 'is_false' | string;
  value?: any;
}

export interface ActionItem {
  type: ActionType | string;
  template?: string | null;
  message?: string | null;
  promotion_code?: string | null;
  points?: number | null;
  tag?: string | null;
  notification_title?: string | null;
  notification_body?: string | null;
  wait_hours?: number | null;
  params?: Record<string, any> | null;
}

export interface WorkflowCreateInput {
  name: string;
  code: string;
  description?: string | null;
  trigger_type: TriggerType | string;
  trigger_config?: Record<string, any>;
  conditions?: ConditionItem[];
  actions?: ActionItem[];
  status?: WorkflowStatus | string;
  is_system_template?: boolean;
}

export interface WorkflowUpdateInput {
  name?: string | null;
  description?: string | null;
  trigger_type?: TriggerType | string | null;
  trigger_config?: Record<string, any> | null;
  conditions?: ConditionItem[] | null;
  actions?: ActionItem[] | null;
  status?: WorkflowStatus | string | null;
}

export interface WorkflowStatusUpdateInput {
  status: WorkflowStatus | string;
}

export interface WorkflowListItem {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  trigger_type: TriggerType | string;
  trigger_config: Record<string, any>;
  conditions: ConditionItem[];
  actions: ActionItem[];
  status: WorkflowStatus | string;
  is_system_template: boolean;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  created_at: string;
  updated_at: string;
}

export interface AutomationRunListItem {
  id: string;
  workflow_id: string;
  workflow_name?: string | null;
  workflow_code?: string | null;
  trigger_type: string;
  trigger_source_id?: string | null;
  status: RunStatus | string;
  started_at: string;
  completed_at?: string | null;
  step_count: number;
  error_message?: string | null;
  created_at: string;
}

export interface WorkflowDetailResponse extends WorkflowListItem {
  recent_runs: AutomationRunListItem[];
}

export interface WorkflowListResponse {
  items: WorkflowListItem[];
  total: number;
}

export interface AutomationOverviewStats {
  total_workflows: number;
  active_workflows: number;
  paused_workflows: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  active_templates_count: number;
}

export interface AutomationRunDetailResponse extends AutomationRunListItem {
  step_runs: Array<{
    step_index: number;
    action_type: string;
    status: string;
    output?: any;
    error?: string | null;
    executed_at: string;
  }>;
  metadata_json: Record<string, any>;
}

export interface AutomationRunListResponse {
  items: AutomationRunListItem[];
  total: number;
}

export interface TriggerDispatchInput {
  trigger_type: string;
  source_id?: string | null;
  context?: Record<string, any>;
}

export interface TriggerDispatchResult {
  trigger_type: string;
  matched_workflows_count: number;
  executed_runs_count: number;
  run_ids: string[];
  summary: string;
}

export interface TestRunInput {
  test_context: Record<string, any>;
}

export interface TestRunResult {
  workflow_id: string;
  workflow_name: string;
  status: string;
  conditions_passed: boolean;
  condition_evaluations: Array<{
    condition: ConditionItem;
    passed: boolean;
    reason: string;
  }>;
  step_runs: Array<{
    step_index: number;
    action_type: string;
    status: string;
    output?: any;
    error?: string | null;
    executed_at: string;
  }>;
  error_message?: string | null;
}

// ==========================================
// AI RECOMMENDATIONS & SMART ALERTS CONTRACTS
// ==========================================

export type RecommendationType =
  | 'INVENTORY_CLEARANCE'
  | 'CAMPAIGN_OPPORTUNITY'
  | 'CUSTOMER_RETENTION'
  | 'CHANNEL_OPTIMIZATION'
  | 'PRICE_PROMO_STRATEGY';

export type RecommendationStatus = 'PENDING' | 'ACCEPTED' | 'DISMISSED' | 'APPLIED';

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export type AlertType =
  | 'EXPIRY_RISK'
  | 'LOW_STOCK'
  | 'HIGH_WASTE'
  | 'ROAS_DROP'
  | 'LOW_MARGIN_RISK'
  | 'REVENUE_ANOMALY';

export interface EvidenceItem {
  metric: string;
  value: any;
  comparison: string;
  source: string;
}

export interface AIRecommendationItem {
  id: string;
  recommendation_type: RecommendationType;
  status: RecommendationStatus;
  title: string;
  problem_statement: string;
  recommended_action: string;
  evidence: EvidenceItem[];
  target_products: Array<{ id?: string; sku?: string; name: string; base_price?: number }>;
  target_customer_segment?: string | null;
  target_channels: string[];
  suggested_promotion?: Record<string, any> | null;
  expected_impact?: Record<string, any> | null;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  risks: string[];
  dismiss_reason?: string | null;
  converted_campaign_id?: string | null;
  converted_workflow_id?: string | null;
  applied_at?: string | null;
  applied_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIRecommendationListResponse {
  items: AIRecommendationItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface RecommendationOverviewStats {
  total_recommendations: number;
  pending_count: number;
  applied_count: number;
  high_confidence_count: number;
  active_alerts_count: number;
  critical_alerts_count: number;
}

export interface ConvertCampaignRequest {
  custom_name?: string | null;
  budget?: number | null;
}

export interface ConvertWorkflowRequest {
  custom_name?: string | null;
}

export interface DismissRecommendationRequest {
  reason?: string | null;
}

export interface GenerateRecommendationsRequest {
  force_regenerate?: boolean;
}

export interface SmartAlertItem {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  entity_type?: string | null;
  entity_id?: string | null;
  metric_data: Record<string, any>;
  action_url?: string | null;
  created_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
}

export interface SmartAlertListResponse {
  items: SmartAlertItem[];
  total: number;
}

export interface SmartAlertSummaryResponse {
  critical: number;
  warning: number;
  info: number;
  total_active: number;
  recent_alerts: SmartAlertItem[];
}

// -------------------------------------------------------------
// Social Media Publishing Engine & Provider Adapters (Prompt 18)
// -------------------------------------------------------------

export type SocialPlatform = 'FACEBOOK' | 'INSTAGRAM' | 'TIKTOK' | 'ZALO_OA' | 'WEBSITE_BLOG';
export type ConnectionStatus = 'CONNECTED' | 'EXPIRED' | 'ERROR' | 'DISCONNECTED';
export type PublishStatus = 'PENDING' | 'QUEUED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED';

export interface SocialConnectionItem {
  id: string;
  platform: SocialPlatform | string;
  account_name: string;
  account_id: string;
  app_id?: string | null;
  token_expires_at?: string | null;
  is_connected: boolean;
  status: ConnectionStatus | string;
  is_mock: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PostMetricItem {
  id: string;
  published_post_id: string;
  recorded_at: string;
  impressions: number;
  reach: number;
  likes: number;
  comments: number;
  shares: number;
  clicks: number;
  conversions: number;
  raw_data_json: Record<string, any>;
  created_at: string;
}

export interface PublishedPostItem {
  id: string;
  content_id: string;
  connection_id?: string | null;
  channel: string;
  external_post_id?: string | null;
  external_post_url?: string | null;
  publish_status: PublishStatus | string;
  scheduled_at?: string | null;
  published_at?: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_at?: string | null;
  error_message?: string | null;
  error_code?: string | null;
  payload_snapshot: Record<string, any>;
  latest_metric?: PostMetricItem | null;
  created_at: string;
  updated_at: string;
}

export interface PublishedPostListResponse {
  items: PublishedPostItem[];
  total: number;
}

export interface PublishNowRequest {
  connection_id?: string | null;
  force_mock?: boolean;
}

export interface PublishNowResponse {
  success: boolean;
  message: string;
  published_post: PublishedPostItem;
}

export interface WorkerBatchResult {
  processed: number;
  published: number;
  retried: number;
  failed: number;
  details: Array<Record<string, any>>;
}

export interface ConnectionTestResult {
  is_valid: boolean;
  status: string;
  message: string;
  account_info?: Record<string, any> | null;
}

export interface TokenRefreshResult {
  success: boolean;
  message: string;
  expires_at?: string | null;
}

// ============================================================================
// AI Provider Abstraction (PROMPT 19)
// ============================================================================

export interface AIProviderHealthResponse {
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | string;
  provider: string;
  model: string;
  latency_ms: number;
  is_mock: boolean;
  message: string;
}

export interface AIProviderInfo {
  name: string;
  type: string;
  default_model: string;
  is_active: boolean;
  description: string;
}

export interface PromptTemplateItem {
  id: string;
  slug: string;
  name: string;
  category: string;
  version: number;
  system_prompt?: string | null;
  user_prompt_template: string;
  input_variables: string[];
  expected_output_schema?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplateListResponse {
  total: number;
  items: PromptTemplateItem[];
}

export interface PromptTemplateCreate {
  slug: string;
  name: string;
  category?: string;
  system_prompt?: string | null;
  user_prompt_template: string;
  input_variables?: string[];
  expected_output_schema?: string | null;
  is_active?: boolean;
}

export interface PromptTemplateUpdate {
  name?: string;
  category?: string;
  system_prompt?: string | null;
  user_prompt_template?: string;
  input_variables?: string[];
  expected_output_schema?: string | null;
  is_active?: boolean;
  bump_version?: boolean;
}

export interface AITestGenerateRequest {
  prompt: string;
  system_prompt?: string | null;
  template_slug?: string | null;
  variables?: Record<string, any> | null;
  temperature?: number;
  max_tokens?: number;
  expect_json?: boolean;
  simulate_behavior?: string | null;
}

export interface AITestGenerateResponse {
  success: boolean;
  text_output?: string | null;
  json_output?: Record<string, any> | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  provider: string;
  model: string;
  log_id?: string | null;
  sanitized_input: string;
  error_message?: string | null;
}

export interface AIGenerationLogItem {
  id: string;
  provider_name: string;
  model_name: string;
  prompt_template_id?: string | null;
  prompt_slug?: string | null;
  prompt_version?: number | null;
  input_prompt_sanitized: string;
  system_prompt_sanitized?: string | null;
  raw_output?: string | null;
  parsed_json?: Record<string, any> | null;
  status: string;
  error_message?: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  retry_count: number;
  created_by_user_id?: string | null;
  created_at: string;
}

export interface AIGenerationLogListResponse {
  total: number;
  items: AIGenerationLogItem[];
}









