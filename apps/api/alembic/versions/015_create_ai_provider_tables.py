"""Create AI provider tables: prompt_templates and ai_generation_logs

Revision ID: 015_ai_provider
Revises: 014_social_publishing
Create Date: 2026-10-08 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_ai_provider'
down_revision = '014_social_publishing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create prompt_templates table
    if 'prompt_templates' not in existing_tables:
        op.create_table(
            'prompt_templates',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False, server_default='GENERAL'),
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('system_prompt', sa.Text(), nullable=True),
            sa.Column('user_prompt_template', sa.Text(), nullable=False),
            sa.Column('input_variables', sa.JSON(), nullable=False),
            sa.Column('expected_output_schema', sa.String(length=100), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_prompt_templates_slug', 'prompt_templates', ['slug'], unique=True)
        op.create_index('ix_prompt_templates_category', 'prompt_templates', ['category'])
        op.create_index('ix_prompt_templates_is_active', 'prompt_templates', ['is_active'])

    # 2. Create ai_generation_logs table
    if 'ai_generation_logs' not in existing_tables:
        op.create_table(
            'ai_generation_logs',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('provider_name', sa.String(length=50), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=False),
            sa.Column('prompt_template_id', sa.String(length=36), sa.ForeignKey('prompt_templates.id', ondelete='SET NULL'), nullable=True),
            sa.Column('prompt_slug', sa.String(length=100), nullable=True),
            sa.Column('prompt_version', sa.Integer(), nullable=True),
            sa.Column('input_prompt_sanitized', sa.Text(), nullable=False),
            sa.Column('system_prompt_sanitized', sa.Text(), nullable=True),
            sa.Column('raw_output', sa.Text(), nullable=True),
            sa.Column('parsed_json', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='SUCCESS'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_ai_logs_provider', 'ai_generation_logs', ['provider_name'])
        op.create_index('ix_ai_logs_prompt_slug', 'ai_generation_logs', ['prompt_slug'])
        op.create_index('ix_ai_logs_status', 'ai_generation_logs', ['status'])
        op.create_index('ix_ai_logs_created_at', 'ai_generation_logs', ['created_at'])
        op.create_index('ix_ai_logs_provider_created', 'ai_generation_logs', ['provider_name', 'created_at'])
        op.create_index('ix_ai_logs_status_created', 'ai_generation_logs', ['status', 'created_at'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'ai_generation_logs' in existing_tables:
        op.drop_table('ai_generation_logs')
    if 'prompt_templates' in existing_tables:
        op.drop_table('prompt_templates')
