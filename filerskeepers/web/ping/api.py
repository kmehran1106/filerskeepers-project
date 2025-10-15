from typing import Annotated

from fastapi import APIRouter, Depends

from filerskeepers.auth.dependencies import get_current_user
from filerskeepers.auth.models import User
from filerskeepers.ping.dtos import PingResponse
from filerskeepers.ping.services import PingService


router = APIRouter()


@router.get("/noauth", response_model=PingResponse)
async def noauth_ping(
    service: Annotated[PingService, Depends()],
) -> PingResponse:
    return await service.health_check()


@router.get(
    "/authenticated",
    response_model=PingResponse,
    summary="Authenticated ping endpoint",
    description="Test endpoint that requires API key authentication",
)
async def authenticated_ping(
    service: Annotated[PingService, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PingResponse:
    return await service.health_check()
