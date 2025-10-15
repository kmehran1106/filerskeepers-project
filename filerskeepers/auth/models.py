import secrets
from datetime import UTC, datetime

import bcrypt
from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    email: Indexed(EmailStr, unique=True)  # type: ignore
    hashed_password: str
    api_key: Indexed(str, unique=True)  # type: ignore
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
        use_state_management = True

    @staticmethod
    def hash_password(password: str) -> str:
        # Convert password to bytes and hash with bcrypt
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str) -> bool:
        # Convert password and stored hash to bytes
        password_bytes = password.encode("utf-8")
        hashed_bytes = self.hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_hex(32)

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(UTC)
