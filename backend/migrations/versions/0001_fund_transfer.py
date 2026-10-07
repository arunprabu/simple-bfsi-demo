"""Create fund transfer customer, account, and transaction tables.

Revision ID: 0001_fund_transfer
Revises:
Create Date: 2026-10-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_fund_transfer"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("customer_id"),
    )
    op.create_table(
        "accounts",
        sa.Column(
            "account_number",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column("customer_id", sa.String(length=128), nullable=False),
        sa.Column(
            "balance",
            sa.Numeric(precision=18, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "balance >= 0",
            name="ck_accounts_balance_nonnegative",
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"]),
        sa.PrimaryKeyConstraint("account_number"),
    )
    op.create_index(
        "ix_accounts_customer_id",
        "accounts",
        ["customer_id"],
        unique=False,
    )
    op.create_table(
        "transactions",
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("from_account", sa.String(length=64), nullable=False),
        sa.Column("to_account", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'COMPLETED'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "from_account <> to_account",
            name="ck_transactions_distinct_accounts",
        ),
        sa.CheckConstraint(
            "amount >= 1.00",
            name="ck_transactions_minimum_amount",
        ),
        sa.CheckConstraint(
            "status = 'COMPLETED'",
            name="ck_transactions_completed_only",
        ),
        sa.ForeignKeyConstraint(["from_account"], ["accounts.account_number"]),
        sa.ForeignKeyConstraint(["to_account"], ["accounts.account_number"]),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index(
        "ix_transactions_created_at",
        "transactions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_from_account",
        "transactions",
        ["from_account"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_from_account", table_name="transactions")
    op.drop_index("ix_transactions_created_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_accounts_customer_id", table_name="accounts")
    op.drop_table("accounts")
    op.drop_table("customers")
