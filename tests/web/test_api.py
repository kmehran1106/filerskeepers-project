import pytest
from httpx import AsyncClient
from tests.base import TestBase

class TestPingApi(TestBase):
    @pytest.fixture(autouse=True)
    def setup(self, client: AsyncClient) -> None:
        self.client = client

    @pytest.mark.anyio
    async def test_ping_endpoint_returns_ok(self) -> None:
        response = await self.client.get("/ping/v1")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
