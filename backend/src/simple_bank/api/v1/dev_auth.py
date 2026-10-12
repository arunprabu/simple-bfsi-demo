from collections.abc import AsyncIterator
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from simple_bank.api.errors import TransferError, TransferErrorCode
from simple_bank.auth.dev_jwt import DEV_JWT_LIFETIME_SECONDS, DevJwtCodec
from simple_bank.config import DatabaseConfigurationError
from simple_bank.db.session import get_async_session
from simple_bank.dev_seed import DEMO_PROFILES, DemoProfile
from simple_bank.models import Customer
from simple_bank.schemas.dev_auth import (
    DemoProfileResponse,
    DemoSignInRequest,
    DevAuthSessionResponse,
)
from simple_bank.schemas.errors import ErrorResponse

router = APIRouter(prefix="/dev-auth", tags=["development authentication"])
DEV_SESSION_COOKIE_NAME = "dev_session"


async def get_optional_dev_auth_session(
    request: Request,
) -> AsyncIterator[AsyncSession | None]:
    if not getattr(request.app.state, "fake_auth_enabled", False):
        yield None
        return

    try:
        async for session in get_async_session():
            yield session
    except (DatabaseConfigurationError, SQLAlchemyError) as exc:
        raise TransferError(TransferErrorCode.DEMO_DATA_UNAVAILABLE) from exc


def _profile_response(profile: DemoProfile) -> DemoProfileResponse:
    return DemoProfileResponse(
        profile_id=profile.profile_id,
        label=profile.label,
    )


def _demo_jwt_codec(request: Request) -> DevJwtCodec:
    codec: DevJwtCodec | None = getattr(request.app.state, "dev_jwt_codec", None)
    if codec is None:
        raise TransferError(TransferErrorCode.FAKE_AUTH_DISABLED)
    return codec


async def _available_profiles(
    session: AsyncSession | None,
) -> list[DemoProfile]:
    if session is None:
        raise TransferError(TransferErrorCode.DEMO_DATA_UNAVAILABLE)
    try:
        available: list[DemoProfile] = []
        for profile in DEMO_PROFILES:
            if await session.get(Customer, profile.customer_id) is not None:
                available.append(profile)
        return available
    except SQLAlchemyError as exc:
        raise TransferError(TransferErrorCode.DEMO_DATA_UNAVAILABLE) from exc


def _current_profile(
    request: Request,
    codec: DevJwtCodec,
    profiles: list[DemoProfile],
) -> DemoProfile | None:
    token = request.cookies.get(DEV_SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        customer_id = codec.verify(token)
    except jwt.InvalidTokenError:
        return None
    return next(
        (profile for profile in profiles if profile.customer_id == customer_id),
        None,
    )


async def _session_status(
    request: Request,
    session: AsyncSession | None,
) -> DevAuthSessionResponse:
    fake_auth_enabled = bool(
        getattr(request.app.state, "fake_auth_enabled", False)
    )
    if not fake_auth_enabled:
        return DevAuthSessionResponse(
            fake_auth_enabled=False,
            authenticated=False,
            profiles=[],
        )

    profiles = await _available_profiles(session)
    codec = _demo_jwt_codec(request)
    current_profile = _current_profile(request, codec, profiles)
    return DevAuthSessionResponse(
        fake_auth_enabled=True,
        authenticated=current_profile is not None,
        profiles=[_profile_response(profile) for profile in profiles],
        current_profile=(
            _profile_response(current_profile) if current_profile is not None else None
        ),
    )


@router.get(
    "/session",
    response_model=DevAuthSessionResponse,
    response_model_exclude_none=True,
    responses={
        503: {
            "model": ErrorResponse,
            "description": "Demo profile data is unavailable.",
        },
    },
)
async def get_dev_auth_session(
    request: Request,
    session: Annotated[
        AsyncSession | None,
        Depends(get_optional_dev_auth_session),
    ],
) -> DevAuthSessionResponse:
    return await _session_status(request, session)


@router.post(
    "/session",
    status_code=status.HTTP_200_OK,
    response_model=DevAuthSessionResponse,
    response_model_exclude_none=True,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Fake sign-in is disabled.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Demo profile is not available.",
        },
        503: {
            "model": ErrorResponse,
            "description": "Demo profile data is unavailable.",
        },
    },
)
async def sign_in_demo(
    payload: DemoSignInRequest,
    request: Request,
    response: Response,
    session: Annotated[
        AsyncSession | None,
        Depends(get_optional_dev_auth_session),
    ],
) -> DevAuthSessionResponse:
    if not getattr(request.app.state, "fake_auth_enabled", False):
        raise TransferError(TransferErrorCode.FAKE_AUTH_DISABLED)

    profile = next(
        (item for item in DEMO_PROFILES if item.profile_id == payload.profile_id),
        None,
    )
    if profile is None:
        raise TransferError(TransferErrorCode.DEMO_PROFILE_NOT_FOUND)

    if session is None:
        raise TransferError(TransferErrorCode.DEMO_DATA_UNAVAILABLE)
    try:
        customer = await session.get(Customer, profile.customer_id)
    except SQLAlchemyError as exc:
        raise TransferError(TransferErrorCode.DEMO_DATA_UNAVAILABLE) from exc
    if customer is None:
        raise TransferError(TransferErrorCode.DEMO_PROFILE_NOT_FOUND)

    profiles = await _available_profiles(session)
    token = _demo_jwt_codec(request).issue(profile.customer_id)
    response.set_cookie(
        key=DEV_SESSION_COOKIE_NAME,
        value=token,
        max_age=DEV_JWT_LIFETIME_SECONDS,
        path="/api/v1",
        secure=request.url.scheme == "https",
        httponly=True,
        samesite="lax",
    )
    return DevAuthSessionResponse(
        fake_auth_enabled=True,
        authenticated=True,
        profiles=[_profile_response(item) for item in profiles],
        current_profile=_profile_response(profile),
    )


@router.delete(
    "/session",
    status_code=status.HTTP_200_OK,
    response_model=DevAuthSessionResponse,
    response_model_exclude_none=True,
)
async def sign_out_demo(
    request: Request,
    response: Response,
) -> DevAuthSessionResponse:
    fake_auth_enabled = bool(
        getattr(request.app.state, "fake_auth_enabled", False)
    )
    response.delete_cookie(
        key=DEV_SESSION_COOKIE_NAME,
        path="/api/v1",
        secure=request.url.scheme == "https",
        httponly=True,
        samesite="lax",
    )
    return DevAuthSessionResponse(
        fake_auth_enabled=fake_auth_enabled,
        authenticated=False,
        profiles=(
            [_profile_response(profile) for profile in DEMO_PROFILES]
            if fake_auth_enabled
            else []
        ),
    )
