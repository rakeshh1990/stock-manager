"""Add idempotency key to alert history.

Revision:      0004_alert_history_event_id
Previous:      0003_alerts_and_history
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_alert_history_event_id"
down_revision = "0003_alerts_and_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alert_history", sa.Column("event_id", sa.String(36), nullable=True))
    op.create_index(
        "ix_alert_history_event_id",
        "alert_history",
        ["event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_alert_history_event_id", table_name="alert_history")
    op.drop_column("alert_history", "event_id")