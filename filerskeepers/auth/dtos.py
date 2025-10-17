from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr

from filerskeepers.auth.models import User


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    api_key: str
    created_at: datetime

    @classmethod
    def from_object(cls, user: User) -> Self:
        return cls(
            id=str(user.id),
            email=user.email,
            api_key=user.api_key,
            created_at=user.created_at,
        )


class LoginResponse(BaseModel):
    user: UserResponse
    message: str
