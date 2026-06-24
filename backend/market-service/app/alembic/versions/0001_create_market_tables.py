"""Create price_history and bhavcopy_runs tables

Revision:      0001_create_market_tables
Previous:      None
"""
from alembic import op
import sqlalchemy as sa

revision      = '0001_create_market_tables'
down_revision = None
branch_labels = None
depends_on    = None


def upgrade() -> None:
    op.create_table(
        'price_history',
        sa.Column('id',         sa.Integer(),               primary_key=True),
        sa.Column('symbol',     sa.String(20),              nullable=False),
        sa.Column('trade_date', sa.Date(),                  nullable=False),
        sa.Column('open',       sa.Float(),                 nullable=True),
        sa.Column('high',       sa.Float(),                 nullable=True),
        sa.Column('low',        sa.Float(),                 nullable=True),
        sa.Column('close',      sa.Float(),                 nullable=False),
        sa.Column('volume',     sa.Float(),                 nullable=True),
        sa.Column('series',     sa.String(10),              nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('symbol', 'trade_date', name='uq_price_history_symbol_date'),
    )
    op.create_index('ix_price_history_symbol',      'price_history', ['symbol'])
    op.create_index('ix_price_history_trade_date',  'price_history', ['trade_date'])
    op.create_index('ix_price_history_symbol_date', 'price_history', ['symbol', 'trade_date'])

    op.create_table(
        'bhavcopy_runs',
        sa.Column('id',            sa.Integer(),               primary_key=True),
        sa.Column('trade_date',    sa.Date(),                  nullable=False, unique=True),
        sa.Column('status',        sa.String(20),              nullable=False),
        sa.Column('rows_inserted', sa.Integer(),               nullable=True),
        sa.Column('error',         sa.String(500),             nullable=True),
        sa.Column('ran_at',        sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('bhavcopy_runs')
    op.drop_index('ix_price_history_symbol_date', table_name='price_history')
    op.drop_index('ix_price_history_trade_date',  table_name='price_history')
    op.drop_index('ix_price_history_symbol',      table_name='price_history')
    op.drop_table('price_history')