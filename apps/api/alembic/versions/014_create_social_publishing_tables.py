"""Create social publishing tables: social_connections, published_posts, post_metrics

Revision ID: 014_social_publishing
Revises: 013_recommendations_and_alerts
Create Date: 2026-10-08 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_social_publishing'
down_revision = '013_recommendations_and_alerts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create social_connections table
    if 'social_connections' not in existing_tables:
        op.create_table(
            'social_connections',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('platform', sa.String(length=50), nullable=False),
            sa.Column('account_name', sa.String(length=255), nullable=False),
            sa.Column('account_id', sa.String(length=255), nullable=False),
            sa.Column('app_id', sa.String(length=255), nullable=True),
            sa.Column('access_token', sa.Text(), nullable=True),
            sa.Column('refresh_token', sa.Text(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='CONNECTED'),
            sa.Column('is_mock', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('metadata_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('idx_social_conn_platform_status', 'social_connections', ['platform', 'status'])
        op.create_index('ix_social_connections_platform', 'social_connections', ['platform'])
        op.create_index('ix_social_connections_account_id', 'social_connections', ['account_id'])
        op.create_index('ix_social_connections_status', 'social_connections', ['status'])

    # 2. Create published_posts table
    if 'published_posts' not in existing_tables:
        op.create_table(
            'published_posts',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('content_id', sa.String(length=36), sa.ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False),
            sa.Column('connection_id', sa.String(length=36), sa.ForeignKey('social_connections.id', ondelete='SET NULL'), nullable=True),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('external_post_id', sa.String(length=255), nullable=True),
            sa.Column('external_post_url', sa.String(length=500), nullable=True),
            sa.Column('publish_status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('error_code', sa.String(length=100), nullable=True),
            sa.Column('payload_snapshot', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_published_posts_content_id', 'published_posts', ['content_id'])
        op.create_index('ix_published_posts_connection_id', 'published_posts', ['connection_id'])
        op.create_index('ix_published_posts_channel', 'published_posts', ['channel'])
        op.create_index('ix_published_posts_external_post_id', 'published_posts', ['external_post_id'])
        op.create_index('ix_published_posts_publish_status', 'published_posts', ['publish_status'])
        op.create_index('ix_published_posts_scheduled_at', 'published_posts', ['scheduled_at'])
        op.create_index('ix_published_posts_published_at', 'published_posts', ['published_at'])
        op.create_index('ix_published_posts_next_retry_at', 'published_posts', ['next_retry_at'])
        op.create_index('idx_pub_post_channel_status', 'published_posts', ['channel', 'publish_status'])
        op.create_index('idx_pub_post_due_pickup', 'published_posts', ['publish_status', 'scheduled_at'])
        op.create_index('idx_pub_post_retry_pickup', 'published_posts', ['publish_status', 'next_retry_at'])

    # 3. Create post_metrics table
    if 'post_metrics' not in existing_tables:
        op.create_table(
            'post_metrics',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('published_post_id', sa.String(length=36), sa.ForeignKey('published_posts.id', ondelete='CASCADE'), nullable=False),
            sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('reach', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('likes', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('comments', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('shares', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('conversions', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('raw_data_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_post_metrics_published_post_id', 'post_metrics', ['published_post_id'])
        op.create_index('ix_post_metrics_recorded_at', 'post_metrics', ['recorded_at'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'post_metrics' in existing_tables:
        op.drop_table('post_metrics')

    if 'published_posts' in existing_tables:
        op.drop_table('published_posts')

    if 'social_connections' in existing_tables:
        op.drop_table('social_connections')
