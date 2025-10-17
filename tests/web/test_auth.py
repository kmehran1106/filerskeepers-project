import pytest
from httpx import AsyncClient

from tests.base import TestBase


class TestAuthApi(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        client: AsyncClient,
        cleanup: None,
    ) -> None:
        self.client = client

    @pytest.mark.anyio
    async def test_register_success(self) -> None:
        # Given
        request = {
            "email": "test@example.com",
            "password": "securepassword123",
        }

        # When
        response = await self.client.post("/auth/v1/register", json=request)

        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "api_key" in data
        assert len(data["api_key"]) == 64
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.anyio
    async def test_login_success(self) -> None:
        # Given
        register_request = {
            "email": "login@example.com",
            "password": "password123",
        }
        register_response = await self.client.post(
            "/auth/v1/register", json=register_request
        )
        api_key = register_response.json()["api_key"]

        # When
        login_request = {
            "email": "login@example.com",
            "password": "password123",
        }
        response = await self.client.post("/auth/v1/login", json=login_request)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert data["user"]["email"] == "login@example.com"
        assert data["user"]["api_key"] == api_key
