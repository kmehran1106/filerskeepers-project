from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from filerskeepers.auth.models import User
from filerskeepers.auth.repositories import UserRepository
from filerskeepers.auth.services import AuthService


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repository=user_repository)


async def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    x_api_key: Annotated[
        str | None, Header(description="API key for authentication")
    ] = None,
) -> User:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    user = await auth_service.verify_api_key(x_api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user
