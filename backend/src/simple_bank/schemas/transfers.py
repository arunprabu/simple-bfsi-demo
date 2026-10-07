from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class TransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_account: StrictStr = Field(min_length=1)
    to_account: StrictStr = Field(min_length=1)
    amount: StrictStr


class TransferResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1)
    status: Literal["COMPLETED"]
    from_account: str = Field(pattern=r"^XXXX[0-9]{4}$")
    to_account: str = Field(pattern=r"^XXXX[0-9]{4}$")
    amount: str = Field(pattern=r"^[0-9]+\.[0-9]{2}$")
    created_at: datetime
