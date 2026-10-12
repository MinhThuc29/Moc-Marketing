"""Create AI recommendations and smart alerts tables

Revision ID: 013_recommendations_and_alerts
Revises: 012_marketing_automation
Create Date: 2026-10-08 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_recommendations_and_alerts'
down_revision = '012_marketing_automation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create ai_recommendations table
    if 'ai_recommendations' not in existing_tables:
        op.create_table(
            'ai_recommendations',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('recommendation_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('problem_statement', sa.Text(), nullable=False),
            sa.Column('recommended_action', sa.Text(), nullable=False),
            sa.Column('evidence', sa.JSON(), nullable=False),
            sa.Column('target_products', sa.JSON(), nullable=False),
            sa.Column('target_customer_segment', sa.String(length=50), nullable=True),
            sa.Column('target_channels', sa.JSON(), nullable=False),
            sa.Column('suggested_promotion', sa.JSON(), nullable=True),
            sa.Column('expected_impact', sa.JSON(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
            sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='HIGH'),
            sa.Column('risks', sa.JSON(), nullable=False),
            sa.Column('dismiss_reason', sa.Text(), nullable=True),
            sa.Column('converted_campaign_id', sa.String(length=36), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True),
            sa.Column('converted_workflow_id', sa.String(length=36), sa.ForeignKey('automation_workflows.id', ondelete='SET NULL'), nullable=True),
            sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('applied_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index('ix_ai_recommendations_type', 'ai_recommendations', ['recommendation_type'])
        op.create_index('ix_ai_recommendations_status', 'ai_recommendations', ['status'])
        op.create_index('ix_ai_recommendations_confidence', 'ai_recommendations', ['confidence_level'])
        op.create_index('ix_ai_rec_type_status', 'ai_recommendations', ['recommendation_type', 'status'])
        op.create_index('ix_ai_rec_conf_status', 'ai_recommendations', ['confidence_level', 'status'])

    # 2. Create smart_alerts table
    if 'smart_alerts' not in existing_tables:
        op.create_table(
            'smart_alerts',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('alert_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False, server_default='WARNING'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.String(length=100), nullable=True),
            sa.Column('metric_data', sa.JSON(), nullable=False),
            sa.Column('action_url', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('acknowledged_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('resolved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        )
        op.create_index('ix_smart_alerts_type', 'smart_alerts', ['alert_type'])
        op.create_index('ix_smart_alerts_severity', 'smart_alerts', ['severity'])
        op.create_index('ix_smart_alerts_status', 'smart_alerts', ['status'])
        op.create_index('ix_smart_alert_sev_status', 'smart_alerts', ['severity', 'status'])
        op.create_index('ix_smart_alert_type_status', 'smart_alerts', ['alert_type', 'status'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'smart_alerts' in existing_tables:
        op.drop_table('smart_alerts')

    if 'ai_recommendations' in existing_tables:
        op.drop_table('ai_recommendations')
