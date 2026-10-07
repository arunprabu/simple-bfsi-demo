"""Add the authoritative account-opening timestamp.

Revision ID: 0002_account_opened_at
Revises: 0001_fund_transfer
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_account_opened_at"
down_revision: Union[str, None] = "0001_fund_transfer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "opened_at")
