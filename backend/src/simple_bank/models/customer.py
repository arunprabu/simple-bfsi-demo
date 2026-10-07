from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(128), primary_key=True)
