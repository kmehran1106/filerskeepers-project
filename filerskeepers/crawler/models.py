from datetime import UTC, datetime
from enum import StrEnum

from beanie import Document
from pydantic import Field


class CrawlStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    IN_PROGRESS = "in_progress"


class CrawlMetadata(Document):
    url: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: CrawlStatus = CrawlStatus.IN_PROGRESS
    books_crawled: int = 0
    errors_count: int = 0
    error_messages: list[str] = Field(default_factory=list)
    last_page_crawled: int = 0  # Last successfully crawled catalog page
    total_pages: int | None = None  # Total pages if known
    is_complete: bool = False  # Whether the crawl finished completely

    class Settings:
        name = "crawl_metadata"
        use_state_management = True
