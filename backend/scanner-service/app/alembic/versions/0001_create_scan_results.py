"""
Create scan_results table — initial schema for the scanner service.

Revision:      0001_create_scan_results
Previous:      None
"""
from alembic import op
import sqlalchemy as sa

revision      = '0001_create_scan_results'
down_revision = None
branch_labels = None
depends_on    = None


def upgrade() -> None:
    op.create_table(
        'scan_results',
        sa.Column('id',             sa.Integer(),                  primary_key=True),
        sa.Column('scan_run_id',    sa.String(36),                 nullable=False),
        sa.Column('user_id',        sa.Integer(),                  nullable=False),
        sa.Column('symbol',         sa.String(20),                 nullable=False),
        sa.Column('score',          sa.Integer(),                  nullable=False),
        sa.Column('recommendation', sa.String(20),                 nullable=False),
        sa.Column('latest_close',   sa.Float(),                    nullable=True),
        sa.Column('rsi',            sa.Float(),                    nullable=True),
        sa.Column('momentum_5d',    sa.Float(),                    nullable=True),
        sa.Column('ma_trend',       sa.String(10),                 nullable=True),
        sa.Column('macd_trend',     sa.String(10),                 nullable=True),
        sa.Column('volume_spike',   sa.Boolean(),                  nullable=True),
        sa.Column('breakout',       sa.Boolean(),                  nullable=True),
        sa.Column('in_watchlist',   sa.Boolean(),                  server_default='false'),
        sa.Column('error',          sa.Text(),                     nullable=True),
        sa.Column('scanned_at',     sa.DateTime(timezone=True),    server_default=sa.func.now()),
    )
    # Index on scan_run_id — used to fetch all results from one scan run
    op.create_index('ix_scan_results_scan_run_id', 'scan_results', ['scan_run_id'])
    # Index on user_id — used to fetch the latest scan for a user
    op.create_index('ix_scan_results_user_id', 'scan_results', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_scan_results_user_id',    table_name='scan_results')
    op.drop_index('ix_scan_results_scan_run_id', table_name='scan_results')
    op.drop_table('scan_results')