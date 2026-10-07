from pydantic import BaseModel, ConfigDict

from simple_bank.api.errors import TransferErrorCode


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: TransferErrorCode
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
