from fastapi import HTTPException, status
from loguru import logger

from filerskeepers.auth.dtos import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from filerskeepers.auth.models import User
from filerskeepers.auth.repositories import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(self, request: RegisterRequest) -> UserResponse:
        # Check if user already exists
        existing_user = await self.user_repository.find_by_email(request.email)
        if existing_user:
            logger.warning(f"Registration failed: user {request.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Validate password
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )

        # Create user
        hashed_password = User.hash_password(request.password)
        api_key = User.generate_api_key()

        user = await self.user_repository.create(
            email=request.email,
            hashed_password=hashed_password,
            api_key=api_key,
        )

        logger.info(f"User registered successfully: {user.email}")

        return UserResponse.from_object(user)

    async def login(self, request: LoginRequest) -> LoginResponse:
        # Find user by email
        user = await self.user_repository.find_by_email(request.email)
        if not user:
            logger.warning(f"Login failed: user {request.email} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not user.verify_password(request.password):
            logger.warning(f"Login failed: invalid password for {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        logger.info(f"User logged in successfully: {user.email}")

        return LoginResponse(
            user=UserResponse.from_object(user), message="Login successful"
        )

    async def verify_api_key(self, api_key: str) -> User | None:
        return await self.user_repository.find_by_api_key(api_key)
