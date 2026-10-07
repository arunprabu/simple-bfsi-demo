from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from simple_bank.api.dependencies import get_authenticated_customer_id
from simple_bank.db.session import get_async_session
from simple_bank.repositories.unit_of_work import SqlAlchemyTransferUnitOfWork
from simple_bank.schemas.errors import ErrorResponse
from simple_bank.schemas.transfers import TransferRequest, TransferResponse
from simple_bank.services.transfers import TransferResult, TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])


async def get_transfer_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TransferService:
    return TransferService(lambda: SqlAlchemyTransferUnitOfWork(session))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid amount or same account."},
        401: {"model": ErrorResponse, "description": "Caller is not authenticated."},
        404: {"model": ErrorResponse, "description": "Account was not found."},
        409: {"model": ErrorResponse, "description": "Transfer is not eligible."},
        500: {"model": ErrorResponse, "description": "Transfer could not complete."},
    },
)
async def create_transfer(
    payload: TransferRequest,
    customer_id: Annotated[str, Depends(get_authenticated_customer_id)],
    service: Annotated[TransferService, Depends(get_transfer_service)],
) -> TransferResponse:
    result: TransferResult = await service.transfer(
        customer_id=customer_id,
        from_account=payload.from_account,
        to_account=payload.to_account,
        amount=payload.amount,
    )
    return TransferResponse(
        transaction_id=result.transaction_id,
        status="COMPLETED",
        from_account=result.from_account,
        to_account=result.to_account,
        amount=format(result.amount, ".2f"),
        created_at=result.created_at,
    )
