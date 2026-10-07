"""Require the backfilled account-opening timestamp.

Revision ID: 0003_require_account_opened_at
Revises: 0002_account_opened_at
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_require_account_opened_at"
down_revision: Union[str, None] = "0002_account_opened_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    has_unbackfilled_accounts = op.get_bind().execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM accounts WHERE opened_at IS NULL)")
    ).scalar_one()
    if has_unbackfilled_accounts:
        raise RuntimeError(
            "Cannot require accounts.opened_at while existing accounts are missing "
            "their authoritative opening timestamp. Backfill from the account "
            "source-of-record after revision 0002_account_opened_at, then retry."
        )

    op.alter_column(
        "accounts",
        "opened_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "accounts",
        "opened_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
