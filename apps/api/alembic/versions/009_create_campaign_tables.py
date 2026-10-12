"""Create campaign management tables

Revision ID: 009_campaign_management
Revises: 008_customer_crm
Create Date: 2026-10-07 23:51:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_campaign_management'
down_revision = '008_customer_crm'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create campaigns table
    if 'campaigns' not in existing_tables:
        op.create_table(
            'campaigns',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=150), nullable=False, index=True),
            sa.Column('code', sa.String(length=50), nullable=False, unique=True, index=True),
            sa.Column('objective', sa.String(length=50), server_default='CONVERSION', nullable=False, index=True),
            sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False, index=True),
            sa.Column('start_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('end_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('budget', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('actual_spend', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('revenue_attributed', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('target_audience', sa.JSON(), nullable=True),
            sa.Column('promotion_id', sa.String(length=36), sa.ForeignKey('promotions.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('landing_page', sa.String(length=255), nullable=True),
            sa.Column('utm_source', sa.String(length=100), nullable=True),
            sa.Column('utm_medium', sa.String(length=100), nullable=True),
            sa.Column('utm_campaign', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('approved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 2. Create campaign_channels table
    if 'campaign_channels' not in existing_tables:
        op.create_table(
            'campaign_channels',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('channel_budget', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('channel_spend', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='ACTIVE', nullable=False),
            sa.Column('target_metric', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 3. Create campaign_products table
    if 'campaign_products' not in existing_tables:
        op.create_table(
            'campaign_products',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('is_hero_product', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('special_price', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'campaign_products' in existing_tables:
        op.drop_table('campaign_products')
    if 'campaign_channels' in existing_tables:
        op.drop_table('campaign_channels')
    if 'campaigns' in existing_tables:
        op.drop_table('campaigns')
