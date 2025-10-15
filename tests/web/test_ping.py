import pytest
from httpx import AsyncClient

from tests.base import TestBase


class TestPingApi(TestBase):
    @pytest.fixture(autouse=True)
    def setup(self, client: AsyncClient) -> None:
        self.client = client

    @pytest.mark.anyio
    async def test_ping_endpoint_returns_ok(self) -> None:
        response = await self.client.get("/ping/v1/noauth")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.anyio
    async def test_authenticated_ping_success(self) -> None:
        # Given
        register_request = {
            "email": "ping@example.com",
            "password": "password123",
        }
        register_response = await self.client.post(
            "/auth/v1/register", json=register_request
        )
        api_key = register_response.json()["api_key"]

        # When
        response = await self.client.get(
            "/ping/v1/authenticated",
            headers={"X-API-Key": api_key},
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.anyio
    async def test_authenticated_ping_invalid_key(self) -> None:
        # When
        response = await self.client.get(
            "/ping/v1/authenticated",
            headers={"X-API-Key": "invalid-key"},
        )

        # Then
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_authenticated_ping_no_key(self) -> None:
        # When
        response = await self.client.get("/ping/v1/authenticated")

        # Then
        assert response.status_code == 401
        assert "API key is required" in response.json()["detail"]
