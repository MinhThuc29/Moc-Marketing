"""Create customer CRM and loyalty tables

Revision ID: 008_customer_crm
Revises: 007_omnichannel_settlement
Create Date: 2026-10-07 23:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_customer_crm'
down_revision = '007_omnichannel_settlement'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create customers table
    if 'customers' not in existing_tables:
        op.create_table(
            'customers',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('full_name', sa.String(length=100), nullable=False, index=True),
            sa.Column('phone', sa.String(length=20), nullable=False, unique=True, index=True),
            sa.Column('email', sa.String(length=120), nullable=True, index=True),
            sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
            sa.Column('default_address', sa.Text(), nullable=True),
            sa.Column('source', sa.String(length=30), server_default='ONLINE', nullable=False, index=True),
            sa.Column('segment', sa.String(length=30), server_default='NEW', nullable=False, index=True),
            sa.Column('first_order_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_order_at', sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column('order_count', sa.Integer(), server_default='0', nullable=False, index=True),
            sa.Column('total_spent', sa.Numeric(precision=12, scale=2), server_default='0.0', nullable=False, index=True),
            sa.Column('average_order_value', sa.Numeric(precision=12, scale=2), server_default='0.0', nullable=False),
            sa.Column('loyalty_points', sa.Integer(), server_default='0', nullable=False, index=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('consent_marketing', sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 2. Create customer_addresses table
    if 'customer_addresses' not in existing_tables:
        op.create_table(
            'customer_addresses',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('customer_id', sa.String(length=36), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('receiver_name', sa.String(length=100), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=False),
            sa.Column('address_line', sa.Text(), nullable=False),
            sa.Column('district', sa.String(length=50), nullable=True),
            sa.Column('city', sa.String(length=50), server_default='Hồ Chí Minh', nullable=False),
            sa.Column('is_default', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 3. Create loyalty_transactions table
    if 'loyalty_transactions' not in existing_tables:
        op.create_table(
            'loyalty_transactions',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('customer_id', sa.String(length=36), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('order_id', sa.String(length=36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('transaction_type', sa.String(length=20), server_default='EARN', nullable=False),
            sa.Column('points', sa.Integer(), nullable=False),
            sa.Column('balance_after', sa.Integer(), nullable=False),
            sa.Column('reason', sa.String(length=255), nullable=False),
            sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        )

    # 4. Add customer_id column to orders table if not present
    if 'orders' in existing_tables:
        order_cols = [c['name'] for c in inspector.get_columns('orders')]
        if 'customer_id' not in order_cols:
            op.add_column('orders', sa.Column('customer_id', sa.String(length=36), nullable=True))
            try:
                op.create_foreign_key('fk_orders_customer_id', 'orders', 'customers', ['customer_id'], ['id'], ondelete='SET NULL')
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'loyalty_transactions' in existing_tables:
        op.drop_table('loyalty_transactions')
    if 'customer_addresses' in existing_tables:
        op.drop_table('customer_addresses')
    if 'customers' in existing_tables:
        op.drop_table('customers')
