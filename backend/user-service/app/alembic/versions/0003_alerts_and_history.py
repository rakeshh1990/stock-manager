"""Add alerts and alert_history tables

Revision:      0003_alerts_and_history
Previous:      0002_watchlist_redesign
"""
from alembic import op
import sqlalchemy as sa

revision      = '0003_alerts_and_history'
down_revision = '0002_watchlist_redesign'
branch_labels = None
depends_on    = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('id',             sa.Integer(),               primary_key=True),
        sa.Column('user_id',        sa.Integer(),               nullable=False),
        sa.Column('symbol',         sa.String(20),              nullable=False),
        sa.Column('alert_type',     sa.String(20),              nullable=False, server_default='condition'),
        sa.Column('condition_type', sa.String(20),              nullable=False),
        sa.Column('threshold',      sa.Numeric(12, 2),          nullable=True),
        sa.Column('active',         sa.String(1),               nullable=False, server_default='Y'),
        sa.Column('cooldown_hours', sa.Integer(),               server_default='24'),
        sa.Column('created_at',     sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_fired_at',  sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])

    op.create_table(
        'alert_history',
        sa.Column('id',              sa.Integer(),               primary_key=True),
        sa.Column('alert_id',        sa.Integer(),               sa.ForeignKey('alerts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id',         sa.Integer(),               nullable=False),
        sa.Column('symbol',          sa.String(20),              nullable=False),
        sa.Column('alert_type',      sa.String(20),              nullable=False),
        sa.Column('condition_type',  sa.String(20),              nullable=False),
        sa.Column('triggered_value', sa.Numeric(12, 4),          nullable=True),
        sa.Column('threshold',       sa.Numeric(12, 2),          nullable=True),
        sa.Column('message',         sa.String(500),             nullable=False),
        sa.Column('priority',        sa.String(10),              nullable=False, server_default='normal'),
        sa.Column('read',            sa.String(1),               nullable=False, server_default='N'),
        sa.Column('fired_at',        sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_alert_history_user_id', 'alert_history', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_alert_history_user_id', table_name='alert_history')
    op.drop_table('alert_history')
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_table('alerts')