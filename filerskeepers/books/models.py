from datetime import UTC, datetime
from typing import Literal

from beanie import Document, Indexed
from pydantic import Field


class Book(Document):
    name: Indexed(str)  # type: ignore
    description: str = ""
    category: Indexed(str)  # type: ignore
    price_excl_tax: float
    price_incl_tax: float
    availability: Indexed(str)  # type: ignore
    num_reviews: int = 0
    image_url: str
    rating: Indexed(int)  # type: ignore

    source_url: str
    crawl_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    crawl_status: Literal["success", "failed", "partial"] = "success"

    html_snapshot: str = ""

    content_hash: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "books"
        use_state_management = True
        indexes = [
            "name",
            "category",
            "rating",
            "availability",
            "content_hash",
        ]

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(UTC)


class ChangeLog(Document):
    book_id: Indexed(str)  # type: ignore
    book_name: str
    change_type: Literal["new_book", "price_change", "availability_change", "other"]
    old_value: str | None = None
    new_value: str | None = None
    field_changed: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "change_logs"
        use_state_management = True
        indexes = [
            "book_id",
            "change_type",
            "timestamp",
        ]
