import pytest
from fastapi import HTTPException

from filerskeepers.auth.dtos import LoginRequest, RegisterRequest
from filerskeepers.auth.services import AuthService
from tests.base import TestBase


class TestAuthService(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        auth_service: AuthService,
        cleanup: None,
    ) -> None:
        self.auth_service = auth_service

    @pytest.mark.anyio
    async def test_register_success(self) -> None:
        # Given
        request = RegisterRequest(
            email="test@example.com",
            password="securepassword123",
        )

        # When
        response = await self.auth_service.register(request)

        # Then
        assert response.email == "test@example.com"
        assert len(response.api_key) == 64
        assert response.id is not None
        assert response.created_at is not None

    @pytest.mark.anyio
    async def test_register_duplicate_email(self) -> None:
        # Given
        request = RegisterRequest(
            email="duplicate@example.com",
            password="password123",
        )
        await self.auth_service.register(request)

        # When/Then
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.register(request)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_register_short_password(self) -> None:
        # Given
        request = RegisterRequest(
            email="test@example.com",
            password="short",
        )

        # When/Then
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.register(request)

        assert exc_info.value.status_code == 400
        assert "at least 8 characters" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_login_success(self) -> None:
        # Given
        register_request = RegisterRequest(
            email="login@example.com",
            password="password123",
        )
        register_response = await self.auth_service.register(register_request)

        # When
        login_request = LoginRequest(
            email="login@example.com",
            password="password123",
        )
        response = await self.auth_service.login(login_request)

        # Then
        assert response.message == "Login successful"
        assert response.user.email == "login@example.com"
        assert response.user.api_key == register_response.api_key
        assert response.user.id == register_response.id

    @pytest.mark.anyio
    async def test_login_wrong_password(self) -> None:
        # Given
        register_request = RegisterRequest(
            email="user@example.com",
            password="correctpassword",
        )
        await self.auth_service.register(register_request)

        # When/Then
        login_request = LoginRequest(
            email="user@example.com",
            password="wrongpassword",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.login(login_request)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_login_nonexistent_user(self) -> None:
        # Given/When/Then
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="password123",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.login(login_request)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_verify_api_key_success(self) -> None:
        # Given
        register_request = RegisterRequest(
            email="verify@example.com",
            password="password123",
        )
        register_response = await self.auth_service.register(register_request)

        # When
        user = await self.auth_service.verify_api_key(register_response.api_key)

        # Then
        assert user is not None
        assert user.email == "verify@example.com"
        assert user.api_key == register_response.api_key

    @pytest.mark.anyio
    async def test_verify_api_key_invalid(self) -> None:
        # Given
        invalid_api_key = "invalid_api_key_that_does_not_exist"

        # When
        user = await self.auth_service.verify_api_key(invalid_api_key)

        # Then
        assert user is None
