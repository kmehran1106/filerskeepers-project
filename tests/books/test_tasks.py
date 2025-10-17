import pytest

from filerskeepers.books.models import Book
from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.books.tasks import process_crawled_book
from filerskeepers.queue.base import WorkerContext
from tests.base import TestBase


class TestBooksTask(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        worker_context: WorkerContext,
        book_repository: BookRepository,
        change_log_repository: ChangeLogRepository,
        cleanup: None,
    ) -> None:
        self.worker_ctx = worker_context
        self.book_repo = book_repository
        self.change_log_repo = change_log_repository

    @pytest.mark.anyio
    async def test_process_crawled_book_creates_new_book(self) -> None:
        # Given - new book data
        book_data = {
            "name": "New Test Book",
            "description": "A brand new test book",
            "category": "Fiction",
            "price_excl_tax": 10.0,
            "price_incl_tax": 12.0,
            "availability": "In stock",
            "num_reviews": 5,
            "image_url": "http://example.com/image.jpg",
            "rating": 4,
            "source_url": "http://example.com/new-book",
            "html_snapshot": "<html>test</html>",
            "content_hash": "new_hash_123",
        }

        # When
        result = await process_crawled_book(self.worker_ctx, book_data)

        # Then
        assert result["status"] == "created"
        assert "book_id" in result

        # Verify book was created in database
        book = await self.book_repo.find_by_url("http://example.com/new-book")
        assert book is not None
        assert book.name == "New Test Book"
        assert book.category == "Fiction"

        # Verify change log was created
        changes, total = await self.change_log_repo.list_changes(
            book_id=str(book.id), limit=10
        )
        assert total == 1
        assert changes[0].change_type == "new_book"

    @pytest.mark.anyio
    async def test_process_crawled_book_updates_existing_book(self) -> None:
        # Given - existing book
        existing_book = Book(
            name="Existing Book",
            description="Original description",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=12.0,
            availability="In stock",
            num_reviews=5,
            image_url="http://example.com/image.jpg",
            rating=4,
            source_url="http://example.com/existing-book",
            content_hash="old_hash",
        )
        await self.book_repo.create(existing_book)

        # Updated book data with price change
        updated_book_data = {
            "name": "Existing Book",
            "description": "Original description",
            "category": "Fiction",
            "price_excl_tax": 15.0,  # Changed
            "price_incl_tax": 18.0,  # Changed
            "availability": "In stock",
            "num_reviews": 5,
            "image_url": "http://example.com/image.jpg",
            "rating": 4,
            "source_url": "http://example.com/existing-book",
            "html_snapshot": "<html>test</html>",
            "content_hash": "new_hash",  # Changed
        }

        # When
        result = await process_crawled_book(self.worker_ctx, updated_book_data)

        # Then
        assert result["status"] == "updated"
        assert result["book_id"] == str(existing_book.id)

        # Verify book was updated
        book = await self.book_repo.find_by_url("http://example.com/existing-book")
        assert book is not None
        assert book.price_excl_tax == 15.0
        assert book.price_incl_tax == 18.0
        assert book.content_hash == "new_hash"

        # Verify change logs were created for price changes
        changes, total = await self.change_log_repo.list_changes(
            book_id=str(book.id), limit=10
        )
        assert total >= 2  # At least 2 price changes logged

    @pytest.mark.anyio
    async def test_process_crawled_book_returns_unchanged_for_no_changes(self) -> None:
        # Given - existing book with same content hash
        existing_book = Book(
            name="Unchanged Book",
            description="Same description",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=12.0,
            availability="In stock",
            num_reviews=5,
            image_url="http://example.com/image.jpg",
            rating=4,
            source_url="http://example.com/unchanged-book",
            content_hash="same_hash",
        )
        await self.book_repo.create(existing_book)

        # Same book data
        book_data = {
            "name": "Unchanged Book",
            "description": "Same description",
            "category": "Fiction",
            "price_excl_tax": 10.0,
            "price_incl_tax": 12.0,
            "availability": "In stock",
            "num_reviews": 5,
            "image_url": "http://example.com/image.jpg",
            "rating": 4,
            "source_url": "http://example.com/unchanged-book",
            "html_snapshot": "<html>test</html>",
            "content_hash": "same_hash",
        }

        # When
        result = await process_crawled_book(self.worker_ctx, book_data)

        # Then
        assert result["status"] == "unchanged"
        assert result["book_id"] == str(existing_book.id)

        # Verify no new change logs were created
        changes, total = await self.change_log_repo.list_changes(
            book_id=str(existing_book.id), limit=10
        )
        assert total == 0

    @pytest.mark.anyio
    async def test_process_crawled_book_handles_errors(self) -> None:
        # Given - invalid book data (missing required fields)
        invalid_book_data = {
            "name": "Invalid Book",
            # Missing other required fields
        }

        # When
        result = await process_crawled_book(self.worker_ctx, invalid_book_data)

        # Then
        assert result["status"] == "error"
        assert "error" in result
