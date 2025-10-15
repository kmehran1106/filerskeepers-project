import pytest
from httpx import AsyncClient

from tests.base import TestBase


class TestAuthApi(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        client: AsyncClient,
        cleanup: None,
    ) -> AsyncClient:
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
    async def test_register_duplicate_email(self) -> None:
        # Given
        request = {
            "email": "duplicate@example.com",
            "password": "password123",
        }
        await self.client.post("/auth/v1/register", json=request)

        # When
        response = await self.client.post("/auth/v1/register", json=request)

        # Then
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_register_short_password(self) -> None:
        # Given
        request = {
            "email": "test@example.com",
            "password": "short",
        }

        # When
        response = await self.client.post("/auth/v1/register", json=request)

        # Then
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_register_invalid_email(self) -> None:
        # Given
        request = {
            "email": "not-an-email",
            "password": "password123",
        }

        # When
        response = await self.client.post("/auth/v1/register", json=request)

        # Then
        assert response.status_code == 422

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

    @pytest.mark.anyio
    async def test_login_wrong_password(self) -> None:
        # Given
        register_request = {
            "email": "user@example.com",
            "password": "correctpassword",
        }
        await self.client.post("/auth/v1/register", json=register_request)

        # When
        login_request = {
            "email": "user@example.com",
            "password": "wrongpassword",
        }
        response = await self.client.post("/auth/v1/login", json=login_request)

        # Then
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self) -> None:
        # Given/When
        login_request = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }
        response = await self.client.post("/auth/v1/login", json=login_request)

        # Then
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
