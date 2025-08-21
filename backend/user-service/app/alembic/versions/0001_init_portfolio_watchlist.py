from alembic import op
import sqlalchemy as sa

revision = '0001_init_portfolio_watchlist'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('symbols', sa.String(), server_default='')
    )
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True, unique=True),
        sa.Column('symbols', sa.String(), server_default='')
    )

def downgrade() -> None:
    op.drop_table('watchlists')
    op.drop_table('portfolios')
