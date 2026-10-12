"""Create promotion and promotion usages tables

Revision ID: 005_promotions
Revises: 004_inventory
Create Date: 2026-10-07 17:42:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_promotions'
down_revision = '004_inventory'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create promotions table
    op.create_table(
        'promotions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('min_order_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('max_discount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('product_scope', sa.String(length=50), server_default='ALL', nullable=False),
        sa.Column('applicable_product_ids', sa.JSON(), nullable=False),
        sa.Column('applicable_category_ids', sa.JSON(), nullable=False),
        sa.Column('buy_x_get_y_config', sa.JSON(), nullable=True),
        sa.Column('combo_config', sa.JSON(), nullable=True),
        sa.Column('customer_scope', sa.String(length=50), server_default='ALL', nullable=False),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('usage_per_customer', sa.Integer(), server_default='1', nullable=True),
        sa.Column('stackable', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_promotions_code'), 'promotions', ['code'], unique=True)
    op.create_index(op.f('ix_promotions_type'), 'promotions', ['type'], unique=False)
    op.create_index(op.f('ix_promotions_status'), 'promotions', ['status'], unique=False)
    op.create_index(op.f('ix_promotions_start_at'), 'promotions', ['start_at'], unique=False)
    op.create_index(op.f('ix_promotions_end_at'), 'promotions', ['end_at'], unique=False)

    # 2. Create promotion_usages table
    op.create_table(
        'promotion_usages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('promotion_id', sa.String(length=36), sa.ForeignKey('promotions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_promotion_usages_promotion_id'), 'promotion_usages', ['promotion_id'], unique=False)
    op.create_index(op.f('ix_promotion_usages_user_id'), 'promotion_usages', ['user_id'], unique=False)
    op.create_index(op.f('ix_promotion_usages_order_id'), 'promotion_usages', ['order_id'], unique=False)
    op.create_index(op.f('ix_promotion_usages_used_at'), 'promotion_usages', ['used_at'], unique=False)


def downgrade() -> None:
    op.drop_table('promotion_usages')
    op.drop_table('promotions')
