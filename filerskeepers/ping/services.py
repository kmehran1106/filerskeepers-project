from loguru import logger

from filerskeepers.ping.dtos import PingResponse


class PingService:
    async def health_check(self) -> PingResponse:
        logger.debug("Health check performed")
        return PingResponse(status="ok")
