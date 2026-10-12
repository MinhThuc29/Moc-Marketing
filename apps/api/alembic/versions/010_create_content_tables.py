"""Create content items table for AI Content Studio and Multi-channel Publisher

Revision ID: 010_content_studio
Revises: 009_campaign_management
Create Date: 2026-10-08 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_content_studio'
down_revision = '009_campaign_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'content_items' not in existing_tables:
        op.create_table(
            'content_items',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('title', sa.String(length=255), nullable=False, index=True),
            sa.Column('content_type', sa.String(length=50), server_default='FACEBOOK_POST', nullable=False, index=True),
            sa.Column('channel', sa.String(length=50), server_default='FACEBOOK', nullable=False, index=True),
            sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False, index=True),
            sa.Column('brand_tone', sa.String(length=50), server_default='FRESH_ENERGETIC', nullable=False),
            sa.Column('hook', sa.String(length=500), nullable=True),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('cta', sa.String(length=500), nullable=True),
            sa.Column('hashtags', sa.JSON(), nullable=False),
            sa.Column('media_asset_ids', sa.JSON(), nullable=False),
            sa.Column('campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('ai_generated', sa.Boolean(), server_default=sa.sql.expression.false(), nullable=False),
            sa.Column('ai_model', sa.String(length=100), nullable=True),
            sa.Column('ai_prompt', sa.Text(), nullable=True),
            sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column('external_post_id', sa.String(length=255), nullable=True, index=True),
            sa.Column('external_post_url', sa.String(length=500), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('metrics', sa.JSON(), nullable=False),
            sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('approved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('idx_content_status_scheduled', 'content_items', ['status', 'scheduled_at'])
        op.create_index('idx_content_channel_status', 'content_items', ['channel', 'status'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'content_items' in existing_tables:
        op.drop_index('idx_content_channel_status', table_name='content_items')
        op.drop_index('idx_content_status_scheduled', table_name='content_items')
        op.drop_table('content_items')
