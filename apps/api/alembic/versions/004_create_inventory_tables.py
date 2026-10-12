"""Create inventory batches and movements tables

Revision ID: 004_inventory
Revises: 003_media_assets
Create Date: 2026-10-07 16:38:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_inventory'
down_revision = '003_media_assets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add low_stock_threshold to products
    op.add_column(
        'products',
        sa.Column('low_stock_threshold', sa.Integer(), server_default='10', nullable=False)
    )

    # 2. Create inventory_batches table
    op.create_table(
        'inventory_batches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_code', sa.String(length=100), nullable=False),
        sa.Column('quantity_received', sa.Integer(), nullable=False),
        sa.Column('quantity_available', sa.Integer(), nullable=False),
        sa.Column('cost_per_unit', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('supplier', sa.String(length=255), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expiry_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_inventory_batches_product_id'), 'inventory_batches', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_batches_batch_code'), 'inventory_batches', ['batch_code'], unique=True)
    op.create_index(op.f('ix_inventory_batches_expiry_at'), 'inventory_batches', ['expiry_at'], unique=False)
    op.create_index(op.f('ix_inventory_batches_status'), 'inventory_batches', ['status'], unique=False)

    # 3. Create inventory_movements table
    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('batch_id', sa.String(length=36), sa.ForeignKey('inventory_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.String(length=36), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('movement_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('previous_quantity', sa.Integer(), nullable=False),
        sa.Column('new_quantity', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_inventory_movements_batch_id'), 'inventory_movements', ['batch_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_product_id'), 'inventory_movements', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_movement_type'), 'inventory_movements', ['movement_type'], unique=False)
    op.create_index(op.f('ix_inventory_movements_reference_id'), 'inventory_movements', ['reference_id'], unique=False)
    op.create_index(op.f('ix_inventory_movements_created_at'), 'inventory_movements', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('inventory_movements')
    op.drop_table('inventory_batches')
    op.drop_column('products', 'low_stock_threshold')
