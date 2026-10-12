"""Create tracking events and conversion attribution tables for Marketing Analytics Engine

Revision ID: 011_analytics_and_attribution
Revises: 010_content_studio
Create Date: 2026-10-08 08:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_analytics_and_attribution'
down_revision = '010_content_studio'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create tracking_events table
    if 'tracking_events' not in existing_tables:
        op.create_table(
            'tracking_events',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('event_name', sa.String(length=50), nullable=False, index=True),
            sa.Column('anonymous_id', sa.String(length=100), nullable=False, index=True),
            sa.Column('session_id', sa.String(length=100), nullable=False, index=True),
            sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('customer_id', sa.String(length=36), sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('page_url', sa.String(length=500), nullable=True),
            sa.Column('referrer', sa.String(length=500), nullable=True),
            sa.Column('utm_source', sa.String(length=100), nullable=True, index=True),
            sa.Column('utm_medium', sa.String(length=100), nullable=True, index=True),
            sa.Column('utm_campaign', sa.String(length=100), nullable=True, index=True),
            sa.Column('utm_content', sa.String(length=100), nullable=True),
            sa.Column('utm_term', sa.String(length=100), nullable=True),
            sa.Column('channel', sa.String(length=50), nullable=True, index=True),
            sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('content_id', sa.String(length=36), sa.ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('event_metadata', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        )
        op.create_index('ix_tracking_session_time', 'tracking_events', ['session_id', 'created_at'])
        op.create_index('ix_tracking_campaign_event', 'tracking_events', ['campaign_id', 'event_name'])
        op.create_index('ix_tracking_channel_event', 'tracking_events', ['channel', 'event_name'])

    # 2. Create conversion_attributions table
    if 'conversion_attributions' not in existing_tables:
        op.create_table(
            'conversion_attributions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('order_number', sa.String(length=50), nullable=False),
            sa.Column('attribution_model', sa.String(length=50), server_default='LAST_TOUCH', nullable=False, index=True),
            sa.Column('confidence', sa.String(length=50), server_default='DETERMINISTIC', nullable=False, index=True),
            sa.Column('first_touch_source', sa.String(length=100), nullable=True),
            sa.Column('last_touch_source', sa.String(length=100), nullable=True),
            sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('campaign_code', sa.String(length=100), nullable=True),
            sa.Column('content_id', sa.String(length=36), sa.ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('touchpoints_count', sa.Integer(), server_default='1', nullable=False),
            sa.Column('order_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('attributed_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('attribution_weight', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('touchpoint_details', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        )
        op.create_index('ix_attr_order_model', 'conversion_attributions', ['order_id', 'attribution_model'])
        op.create_index('ix_attr_campaign_model', 'conversion_attributions', ['campaign_id', 'attribution_model'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'conversion_attributions' in existing_tables:
        op.drop_table('conversion_attributions')

    if 'tracking_events' in existing_tables:
        op.drop_table('tracking_events')
