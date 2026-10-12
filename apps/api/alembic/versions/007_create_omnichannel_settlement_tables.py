"""Create omnichannel and settlement tables

Revision ID: 007_omnichannel_settlement
Revises: 006_cart_orders
Create Date: 2026-10-07 22:36:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_omnichannel_settlement'
down_revision = '006_cart_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    order_cols = [c['name'] for c in inspector.get_columns('orders')]

    # 1. Create marketplace_imports table
    if 'marketplace_imports' not in existing_tables:
        op.create_table(
            'marketplace_imports',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('file_format', sa.String(length=20), server_default='CSV', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='COMPLETED', nullable=False),
            sa.Column('total_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('imported_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('duplicate_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('rejected_rows', sa.Integer(), server_default='0', nullable=False),
            sa.Column('gross_amount_total', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('platform_fee_total', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('merchant_discount_total', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('net_settlement_total', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('error_report_json', sa.Text(), nullable=True),
            sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(op.f('ix_marketplace_imports_channel'), 'marketplace_imports', ['channel'], unique=False)
        op.create_index(op.f('ix_marketplace_imports_status'), 'marketplace_imports', ['status'], unique=False)

    # 2. Add omnichannel columns to orders table directly
    new_cols = [
        ('channel', sa.Column('channel', sa.String(length=50), server_default='WEBSITE', nullable=False)),
        ('external_order_id', sa.Column('external_order_id', sa.String(length=100), nullable=True)),
        ('external_store_id', sa.Column('external_store_id', sa.String(length=100), nullable=True)),
        ('gross_amount', sa.Column('gross_amount', sa.Numeric(precision=14, scale=2), nullable=True)),
        ('merchant_discount', sa.Column('merchant_discount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False)),
        ('platform_discount', sa.Column('platform_discount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False)),
        ('platform_fee', sa.Column('platform_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False)),
        ('other_fee', sa.Column('other_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False)),
        ('net_amount', sa.Column('net_amount', sa.Numeric(precision=14, scale=2), nullable=True)),
        ('settled_at', sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True)),
        ('raw_import_id', sa.Column('raw_import_id', sa.String(length=36), nullable=True)),
    ]
    for col_name, col_def in new_cols:
        if col_name not in order_cols:
            op.add_column('orders', col_def)

    # 3. Create settlements table
    if 'settlements' not in existing_tables:
        op.create_table(
            'settlements',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('external_settlement_id', sa.String(length=100), nullable=True),
            sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
            sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
            sa.Column('gross_amount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('platform_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('merchant_discount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('other_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('net_amount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='UNMATCHED', nullable=False),
            sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_settlements_channel'), 'settlements', ['channel'], unique=False)
        op.create_index(op.f('ix_settlements_status'), 'settlements', ['status'], unique=False)
        op.create_index(op.f('ix_settlements_external_settlement_id'), 'settlements', ['external_settlement_id'], unique=False)

    # 4. Create settlement_orders table
    if 'settlement_orders' not in existing_tables:
        op.create_table(
            'settlement_orders',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('settlement_id', sa.String(length=36), sa.ForeignKey('settlements.id', ondelete='CASCADE'), nullable=False),
            sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
            sa.Column('allocated_amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('platform_fee', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('merchant_discount', sa.Numeric(precision=14, scale=2), server_default='0.0', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='MATCHED', nullable=False),
            sa.Column('matched_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(op.f('ix_settlement_orders_settlement_id'), 'settlement_orders', ['settlement_id'], unique=False)
        op.create_index(op.f('ix_settlement_orders_order_id'), 'settlement_orders', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_table('settlement_orders')
    op.drop_table('settlements')
    op.drop_table('marketplace_imports')
