"""Create product and category tables

Revision ID: 002_product_category
Revises: 001_auth_rbac
Create Date: 2026-10-07 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_product_category'
down_revision = '001_auth_rbac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. categories
    op.create_table(
        'categories',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=True)

    # 2. products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.String(length=36), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('base_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('cost_price', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('unit', sa.String(length=50), server_default='phần', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False),
        sa.Column('featured', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('ingredients', sa.Text(), nullable=True),
        sa.Column('allergens', sa.Text(), nullable=True),
        sa.Column('nutrition_text', sa.Text(), nullable=True),
        sa.Column('preparation_note', sa.Text(), nullable=True),
        sa.Column('storage_note', sa.Text(), nullable=True),
        sa.Column('shelf_life', sa.String(length=100), nullable=True),
        sa.Column('thumbnail', sa.String(length=500), nullable=True),
        sa.Column('media', sa.JSON(), nullable=False),
        sa.Column('seo_title', sa.String(length=255), nullable=True),
        sa.Column('seo_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=True)
    op.create_index(op.f('ix_products_slug'), 'products', ['slug'], unique=True)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_status'), 'products', ['status'], unique=False)
    op.create_index(op.f('ix_products_featured'), 'products', ['featured'], unique=False)

    # 3. price_audit_logs
    op.create_table(
        'price_audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_base_price', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('new_base_price', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('old_sale_price', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('new_sale_price', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('changed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('change_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_price_audit_logs_product_id'), 'price_audit_logs', ['product_id'], unique=False)
    op.create_index(op.f('ix_price_audit_logs_created_at'), 'price_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('price_audit_logs')
    op.drop_table('products')
    op.drop_table('categories')
