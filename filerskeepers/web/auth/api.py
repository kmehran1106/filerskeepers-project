from typing import Annotated

from fastapi import APIRouter, Depends, status

from filerskeepers.auth.dependencies import get_auth_service
from filerskeepers.auth.dtos import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from filerskeepers.auth.services import AuthService


auth_router = APIRouter()


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password",
)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    return await auth_service.register(request)


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password",
)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return await auth_service.login(request)
