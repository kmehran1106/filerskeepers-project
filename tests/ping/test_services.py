import pytest

from filerskeepers.ping.dtos import PingResponse
from filerskeepers.ping.services import PingService
from tests.base import TestBase

class TestPingService(TestBase):
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = PingService()

    @pytest.mark.anyio
    async def test_health_check_returns_ok_status(self) -> None:
        result = await self.service.health_check()

        assert isinstance(result, PingResponse)
        assert result.status == "ok"
