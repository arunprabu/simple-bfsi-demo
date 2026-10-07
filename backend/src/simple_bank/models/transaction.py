import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "from_account <> to_account",
            name="ck_transactions_distinct_accounts",
        ),
        CheckConstraint("amount >= 1.00", name="ck_transactions_minimum_amount"),
        CheckConstraint(
            "status = 'COMPLETED'",
            name="ck_transactions_completed_only",
        ),
        Index("ix_transactions_created_at", "created_at"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    from_account: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("accounts.account_number"),
        nullable=False,
        index=True,
    )
    to_account: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("accounts.account_number"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2, asdecimal=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'COMPLETED'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
