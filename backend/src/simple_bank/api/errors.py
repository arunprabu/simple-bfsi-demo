from enum import Enum

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class TransferErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    SAME_ACCOUNT = "SAME_ACCOUNT"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    TRANSFER_FAILED = "TRANSFER_FAILED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FAKE_AUTH_DISABLED = "FAKE_AUTH_DISABLED"
    DEMO_PROFILE_NOT_FOUND = "DEMO_PROFILE_NOT_FOUND"
    DEMO_DATA_UNAVAILABLE = "DEMO_DATA_UNAVAILABLE"


ERROR_STATUS_CODES: dict[TransferErrorCode, int] = {
    TransferErrorCode.INVALID_REQUEST: 422,
    TransferErrorCode.INVALID_AMOUNT: 400,
    TransferErrorCode.SAME_ACCOUNT: 400,
    TransferErrorCode.ACCOUNT_NOT_FOUND: 404,
    TransferErrorCode.ACCOUNT_INACTIVE: 409,
    TransferErrorCode.INSUFFICIENT_BALANCE: 409,
    TransferErrorCode.DAILY_LIMIT_EXCEEDED: 409,
    TransferErrorCode.TRANSFER_FAILED: 500,
    TransferErrorCode.UNAUTHENTICATED: 401,
    TransferErrorCode.FAKE_AUTH_DISABLED: 403,
    TransferErrorCode.DEMO_PROFILE_NOT_FOUND: 404,
    TransferErrorCode.DEMO_DATA_UNAVAILABLE: 503,
}

ERROR_MESSAGES: dict[TransferErrorCode, str] = {
    TransferErrorCode.INVALID_REQUEST: (
        "The request is not valid. Check the request fields and try again."
    ),
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
    TransferErrorCode.FAKE_AUTH_DISABLED: (
        "Demo sign-in is not enabled in this environment."
    ),
    TransferErrorCode.DEMO_PROFILE_NOT_FOUND: (
        "The selected demo profile is not available."
    ),
    TransferErrorCode.DEMO_DATA_UNAVAILABLE: (
        "Demo sign-in data is temporarily unavailable."
    ),
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


def _error_response(code: TransferErrorCode, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=ERROR_STATUS_CODES[code],
        content={"error": {"code": code.value, "message": message}},
    )


async def transfer_exception_handler(
    _request: Request,
    exc: TransferError,
) -> JSONResponse:
    return _error_response(exc.code, exc.message)


async def request_validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    # FastAPI's default body echoes the submitted input, which can include full
    # account numbers, so never forward the validation details to the caller.
    return _error_response(
        TransferErrorCode.INVALID_REQUEST,
        ERROR_MESSAGES[TransferErrorCode.INVALID_REQUEST],
    )
