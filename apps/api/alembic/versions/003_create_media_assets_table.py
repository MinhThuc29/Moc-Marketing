"""Create media assets table

Revision ID: 003_media_assets
Revises: 002_product_category
Create Date: 2026-10-07 15:58:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_media_assets'
down_revision = '002_product_category'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'media_assets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('folder', sa.String(length=50), server_default='products', nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_media_assets_filename'), 'media_assets', ['filename'], unique=True)
    op.create_index(op.f('ix_media_assets_mime_type'), 'media_assets', ['mime_type'], unique=False)
    op.create_index(op.f('ix_media_assets_folder'), 'media_assets', ['folder'], unique=False)
    op.create_index(op.f('ix_media_assets_created_at'), 'media_assets', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('media_assets')
