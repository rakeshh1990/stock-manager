"""
Watchlist redesign: replace single-row comma-separated watchlists
with a proper relational watchlists + watchlist_items table pair.

Revision:      0002_watchlist_redesign
Previous:      0001_init_portfolio_watchlist
"""
from alembic import op
import sqlalchemy as sa

revision      = '0002_watchlist_redesign'
down_revision = '0001_init_portfolio_watchlist'
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # Drop the old single-row watchlists table (had user_id unique constraint,
    # stored symbols as a comma-separated string — not scalable).
    op.drop_table("watchlists")

    # Create proper watchlists table — one row per named watchlist.
    op.create_table(
        "watchlists",
        sa.Column("id",         sa.Integer(),                  primary_key=True),
        sa.Column("user_id",    sa.Integer(),                  nullable=False),
        sa.Column("name",       sa.String(100),                nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),    server_default=sa.func.now()),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"])
    op.create_unique_constraint(
        "uq_watchlist_user_name", "watchlists", ["user_id", "name"]
    )

    # Create watchlist_items — one row per symbol per watchlist.
    op.create_table(
        "watchlist_items",
        sa.Column("id",           sa.Integer(),               primary_key=True),
        sa.Column("watchlist_id", sa.Integer(),               sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol",       sa.String(20),              nullable=False),
        sa.Column("notes",        sa.String(500),             nullable=True),
        sa.Column("target_price", sa.Numeric(12, 2),          nullable=True),
        sa.Column("added_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_watchlist_item_symbol", "watchlist_items", ["watchlist_id", "symbol"]
    )


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")

    # Restore the original single-row watchlists table
    op.create_table(
        "watchlists",
        sa.Column("id",      sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True, unique=True),
        sa.Column("symbols", sa.String(),  server_default=""),
    )