from fastapi import APIRouter

from simple_bank.api.v1.transfers import router as transfers_router

api_router = APIRouter()
api_router.include_router(transfers_router)
