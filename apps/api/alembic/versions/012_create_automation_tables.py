"""Create marketing automation workflows and execution run tables

Revision ID: 012_marketing_automation
Revises: 011_analytics_and_attribution
Create Date: 2026-10-08 09:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_marketing_automation'
down_revision = '011_analytics_and_attribution'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create automation_workflows table
    if 'automation_workflows' not in existing_tables:
        op.create_table(
            'automation_workflows',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('code', sa.String(length=100), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('trigger_type', sa.String(length=50), nullable=False),
            sa.Column('trigger_config', sa.JSON(), nullable=False),
            sa.Column('conditions', sa.JSON(), nullable=False),
            sa.Column('actions', sa.JSON(), nullable=False),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
            sa.Column('is_system_template', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('total_runs', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('successful_runs', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('failed_runs', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_automation_workflows_code', 'automation_workflows', ['code'], unique=True)
        op.create_index('ix_automation_workflows_trigger_type', 'automation_workflows', ['trigger_type'])
        op.create_index('ix_automation_workflows_status', 'automation_workflows', ['status'])
        op.create_index('ix_workflows_trigger_status', 'automation_workflows', ['trigger_type', 'status'])
        op.create_index('ix_workflows_template', 'automation_workflows', ['is_system_template'])

    # 2. Create automation_runs table
    if 'automation_runs' not in existing_tables:
        op.create_table(
            'automation_runs',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('workflow_id', sa.String(length=36), sa.ForeignKey('automation_workflows.id', ondelete='CASCADE'), nullable=False),
            sa.Column('trigger_type', sa.String(length=50), nullable=False),
            sa.Column('trigger_source_id', sa.String(length=100), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='RUNNING'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('step_runs', sa.JSON(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_automation_runs_workflow_id', 'automation_runs', ['workflow_id'])
        op.create_index('ix_automation_runs_status', 'automation_runs', ['status'])
        op.create_index('ix_runs_wf_status', 'automation_runs', ['workflow_id', 'status'])
        op.create_index('ix_runs_created_at', 'automation_runs', ['created_at'])


def downgrade() -> None:
    op.drop_table('automation_runs')
    op.drop_table('automation_workflows')
