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


class FailedParse(Document):
    crawl_id: str | None = None
    url: str
    html: str | None = None  # None when fetch failed, populated when parse failed
    failure_reason: str  # Description of why it failed
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "failed_parses"
        use_state_management = True
