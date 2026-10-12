from fastapi import APIRouter

from simple_bank.api.v1.dev_auth import router as dev_auth_router
from simple_bank.api.v1.transfers import router as transfers_router

api_router = APIRouter()
api_router.include_router(dev_auth_router)
api_router.include_router(transfers_router)
