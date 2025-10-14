from typing import Annotated

from fastapi import APIRouter, Depends

from filerskeepers.ping.dtos import PingResponse
from filerskeepers.ping.services import PingService


router = APIRouter()


@router.get("", response_model=PingResponse)
async def ping(
    service: Annotated[PingService, Depends()],
) -> PingResponse:
    return await service.health_check()
