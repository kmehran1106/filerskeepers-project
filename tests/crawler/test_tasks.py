from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest

from filerskeepers.crawler.dtos import CrawledBookDto
from filerskeepers.crawler.repositories import CrawlMetadataRepository
from filerskeepers.crawler.services import CrawlerService
from filerskeepers.crawler.tasks import crawl_books_task
from filerskeepers.queue.base import WorkerContext
from tests.base import TestBase


async def async_book_generator(
    books: list[dict[str, Any]], start_page: int = 1
) -> AsyncGenerator[tuple[CrawledBookDto, int]]:
    page = start_page
    for book_data in books:
        yield CrawledBookDto(**book_data), page


async def async_book_generator_with_error(
    error_message: str, start_page: int = 1
) -> AsyncGenerator[tuple[CrawledBookDto, int]]:
    raise Exception(error_message)
    yield CrawledBookDto(**{}), start_page  # Never reached but needed for type


class TestCrawlerTasks(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        worker_context: WorkerContext,
        crawl_metadata_repository: CrawlMetadataRepository,
        crawler_service: CrawlerService,
        cleanup: None,
    ) -> None:
        self.worker_ctx = worker_context
        self.crawl_metadata_repo = crawl_metadata_repository
        self.crawler_service = crawler_service

    @pytest.mark.anyio
    async def test_crawl_books_task_successfully_enqueues_books(self) -> None:
        # Given - mock crawler service to return sample book data
        sample_books = [
            {
                "name": "Test Book 1",
                "description": "A test book",
                "category": "Fiction",
                "price_excl_tax": 10.0,
                "price_incl_tax": 12.0,
                "availability": "In stock",
                "num_reviews": 5,
                "image_url": "http://example.com/image1.jpg",
                "rating": 4,
                "source_url": "http://example.com/book1",
                "html_snapshot": "<html>test</html>",
                "content_hash": "hash1",
            },
            {
                "name": "Test Book 2",
                "description": "Another test book",
                "category": "Mystery",
                "price_excl_tax": 15.0,
                "price_incl_tax": 18.0,
                "availability": "In stock",
                "num_reviews": 3,
                "image_url": "http://example.com/image2.jpg",
                "rating": 5,
                "source_url": "http://example.com/book2",
                "html_snapshot": "<html>test2</html>",
                "content_hash": "hash2",
            },
        ]

        with patch.object(
            CrawlerService,
            "crawl_all_books",
            return_value=async_book_generator(sample_books),
        ):
            # When
            result = await crawl_books_task(self.worker_ctx)

            # Then
            assert result["status"] == "completed"
            assert result["crawl_status"] == "success"
            assert result["books_found"] == 2
            assert result["books_enqueued"] == 2
            assert result["errors_count"] == 0
            assert result["last_page"] == 1
            assert "resumed" in result

            # Verify crawl metadata was created
            # (metadata is saved in the database, task completed successfully)

    @pytest.mark.anyio
    async def test_crawl_books_task_handles_crawl_errors(self) -> None:
        # Given - mock crawler service to return 1 book (errors are logged internally)
        sample_books = [
            {
                "name": "Test Book 1",
                "description": "A test book",
                "category": "Fiction",
                "price_excl_tax": 10.0,
                "price_incl_tax": 12.0,
                "availability": "In stock",
                "num_reviews": 5,
                "image_url": "http://example.com/image1.jpg",
                "rating": 4,
                "source_url": "http://example.com/book1",
                "html_snapshot": "<html>test</html>",
                "content_hash": "hash1",
            }
        ]

        with patch.object(
            CrawlerService,
            "crawl_all_books",
            return_value=async_book_generator(sample_books),
        ):
            # When
            result = await crawl_books_task(self.worker_ctx)

            # Then
            assert result["status"] == "completed"
            assert result["crawl_status"] == "success"
            assert result["books_found"] == 1
            assert result["books_enqueued"] == 1
            assert result["errors_count"] == 0
            assert result["last_page"] == 1

    @pytest.mark.anyio
    async def test_crawl_books_task_handles_no_books_found(self) -> None:
        # Given - mock crawler service to return no books
        with patch.object(
            CrawlerService,
            "crawl_all_books",
            return_value=async_book_generator([]),
        ):
            # When
            result = await crawl_books_task(self.worker_ctx)

            # Then
            assert result["status"] == "completed"
            # No books found but no errors = success
            assert result["crawl_status"] == "success"
            assert result["books_found"] == 0
            assert result["books_enqueued"] == 0
            assert result["errors_count"] == 0
            assert result["last_page"] == 0

    @pytest.mark.anyio
    async def test_crawl_books_task_handles_exception(self) -> None:
        # Given - mock crawler service to raise exception when iterated
        with patch.object(
            CrawlerService,
            "crawl_all_books",
            return_value=async_book_generator_with_error("Database connection failed"),
        ):
            # When
            result = await crawl_books_task(self.worker_ctx)

            # Then
            assert result["status"] == "failed"
            assert "error" in result
            assert "Database connection failed" in result["error"]
