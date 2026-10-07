from enum import Enum

from fastapi import Request
from fastapi.responses import JSONResponse


class TransferErrorCode(str, Enum):
    INVALID_AMOUNT = "INVALID_AMOUNT"
    SAME_ACCOUNT = "SAME_ACCOUNT"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    TRANSFER_FAILED = "TRANSFER_FAILED"
    UNAUTHENTICATED = "UNAUTHENTICATED"


ERROR_STATUS_CODES: dict[TransferErrorCode, int] = {
    TransferErrorCode.INVALID_AMOUNT: 400,
    TransferErrorCode.SAME_ACCOUNT: 400,
    TransferErrorCode.ACCOUNT_NOT_FOUND: 404,
    TransferErrorCode.ACCOUNT_INACTIVE: 409,
    TransferErrorCode.INSUFFICIENT_BALANCE: 409,
    TransferErrorCode.DAILY_LIMIT_EXCEEDED: 409,
    TransferErrorCode.TRANSFER_FAILED: 500,
    TransferErrorCode.UNAUTHENTICATED: 401,
}

ERROR_MESSAGES: dict[TransferErrorCode, str] = {
    TransferErrorCode.INVALID_AMOUNT: (
        "Amount must be at least Rs 1.00 and have no more than two decimal places."
    ),
    TransferErrorCode.SAME_ACCOUNT: "Source and recipient accounts must be different.",
    TransferErrorCode.ACCOUNT_NOT_FOUND: "A requested account could not be found.",
    TransferErrorCode.ACCOUNT_INACTIVE: "Both accounts must be active.",
    TransferErrorCode.INSUFFICIENT_BALANCE: (
        "The source account does not have enough available funds."
    ),
    TransferErrorCode.DAILY_LIMIT_EXCEEDED: (
        "The transfer exceeds the applicable source-account or customer-wide "
        "daily transfer limit."
    ),
    TransferErrorCode.TRANSFER_FAILED: (
        "Transfer could not be completed. No funds were moved."
    ),
    TransferErrorCode.UNAUTHENTICATED: "Sign in to make a transfer.",
}


class TransferError(Exception):
    def __init__(
        self,
        code: TransferErrorCode,
        message: str | None = None,
    ) -> None:
        self.code = code
        self.message = message or ERROR_MESSAGES[code]
        super().__init__(self.message)


async def transfer_exception_handler(
    _request: Request,
    exc: TransferError,
) -> JSONResponse:
    return JSONResponse(
        status_code=ERROR_STATUS_CODES[exc.code],
        content={
            "error": {
                "code": exc.code.value,
                "message": exc.message,
            }
        },
    )
