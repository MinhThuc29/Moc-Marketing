"""Create cart and order tables

Revision ID: 006_cart_orders
Revises: 005_promotions
Create Date: 2026-10-07 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_cart_orders'
down_revision = '005_promotions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create carts table
    op.create_table(
        'carts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('cart_token', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('promo_code', sa.String(length=50), nullable=True),
        sa.Column('customer_note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_carts_cart_token'), 'carts', ['cart_token'], unique=True)
    op.create_index(op.f('ix_carts_user_id'), 'carts', ['user_id'], unique=False)
    op.create_index(op.f('ix_carts_status'), 'carts', ['status'], unique=False)

    # 2. Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('cart_id', sa.String(length=36), sa.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_cart_items_cart_id'), 'cart_items', ['cart_id'], unique=False)
    op.create_index(op.f('ix_cart_items_product_id'), 'cart_items', ['product_id'], unique=False)

    # 3. Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_phone', sa.String(length=20), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('delivery_address', sa.String(length=500), nullable=False),
        sa.Column('customer_note', sa.Text(), nullable=True),
        sa.Column('internal_note', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), server_default='STOREFRONT_WEB', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='NEW', nullable=False),
        sa.Column('payment_method', sa.String(length=50), server_default='COD', nullable=False),
        sa.Column('payment_status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
        sa.Column('shipping_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
        sa.Column('shipping_discount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('applied_promo_code', sa.String(length=100), nullable=True),
        sa.Column('idempotency_key', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cart_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_customer_phone'), 'orders', ['customer_phone'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_payment_status'), 'orders', ['payment_status'], unique=False)
    op.create_index(op.f('ix_orders_idempotency_key'), 'orders', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)

    # 4. Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('product_sku', sa.String(length=100), nullable=False),
        sa.Column('product_unit', sa.String(length=50), nullable=False),
        sa.Column('thumbnail', sa.String(length=500), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)

    # 5. Create order_status_history table
    op.create_table(
        'order_status_history',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_order_status_history_order_id'), 'order_status_history', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_table('order_status_history')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('carts')
