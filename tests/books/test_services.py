import pytest

from filerskeepers.books.models import Book
from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.books.services import BookService
from tests.base import TestBase


class TestBookService(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        book_repository: BookRepository,
        change_log_repository: ChangeLogRepository,
        book_service: BookService,
        cleanup: None,
    ) -> None:
        self.book_repo = book_repository
        self.change_log_repo = change_log_repository
        self.service = book_service

    @pytest.mark.anyio
    async def test_get_book_returns_book_when_exists(self) -> None:
        # Given
        book = Book(
            name="Test Book",
            description="Test description",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=12.0,
            availability="In stock",
            num_reviews=5,
            image_url="http://example.com/image.jpg",
            rating=4,
            source_url="http://example.com/book",
            content_hash="test_hash_123",
        )
        await self.book_repo.create(book)

        # When
        result = await self.service.get_book(str(book.id))

        # Then
        assert result is not None
        assert result.id == str(book.id)
        assert result.name == "Test Book"
        assert result.category == "Fiction"

    @pytest.mark.anyio
    async def test_get_book_returns_none_when_not_found(self) -> None:
        # When - using a valid ObjectId format that doesn't exist
        result = await self.service.get_book("507f1f77bcf86cd799439011")

        # Then
        assert result is None

    @pytest.mark.anyio
    async def test_list_books_returns_paginated_results(self) -> None:
        # Given - create 5 books
        books = []
        for i in range(5):
            book = Book(
                name=f"Book {i}",
                description=f"Description {i}",
                category="Fiction",
                price_excl_tax=10.0 + i,
                price_incl_tax=12.0 + i,
                availability="In stock",
                num_reviews=i,
                image_url=f"http://example.com/image{i}.jpg",
                rating=3 + (i % 3),
                source_url=f"http://example.com/book{i}",
                content_hash=f"hash_{i}",
            )
            books.append(book)
        await self.book_repo.bulk_create(books)

        # When
        result = await self.service.list_books(page=1, page_size=3)

        # Then
        assert result.total == 5
        assert len(result.books) == 3
        assert result.page == 1
        assert result.page_size == 3
        assert result.total_pages == 2

    @pytest.mark.anyio
    async def test_list_books_filters_by_category(self) -> None:
        # Given
        fiction_book = Book(
            name="Fiction Book",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=12.0,
            availability="In stock",
            rating=4,
            image_url="http://example.com/fiction.jpg",
            source_url="http://example.com/fiction",
            content_hash="fiction_hash",
        )
        mystery_book = Book(
            name="Mystery Book",
            category="Mystery",
            price_excl_tax=15.0,
            price_incl_tax=18.0,
            availability="In stock",
            rating=5,
            image_url="http://example.com/mystery.jpg",
            source_url="http://example.com/mystery",
            content_hash="mystery_hash",
        )
        await self.book_repo.bulk_create([fiction_book, mystery_book])

        # When
        result = await self.service.list_books(category="Fiction")

        # Then
        assert result.total == 1
        assert result.books[0].category == "Fiction"

    @pytest.mark.anyio
    async def test_list_books_filters_by_price_range(self) -> None:
        # Given
        cheap_book = Book(
            name="Cheap Book",
            category="Fiction",
            price_excl_tax=5.0,
            price_incl_tax=6.0,
            availability="In stock",
            rating=3,
            image_url="http://example.com/cheap.jpg",
            source_url="http://example.com/cheap",
            content_hash="cheap_hash",
        )
        expensive_book = Book(
            name="Expensive Book",
            category="Fiction",
            price_excl_tax=50.0,
            price_incl_tax=60.0,
            availability="In stock",
            rating=5,
            image_url="http://example.com/expensive.jpg",
            source_url="http://example.com/expensive",
            content_hash="expensive_hash",
        )
        await self.book_repo.bulk_create([cheap_book, expensive_book])

        # When
        result = await self.service.list_books(min_price=10.0, max_price=70.0)

        # Then
        assert result.total == 1
        assert result.books[0].name == "Expensive Book"

    @pytest.mark.anyio
    async def test_list_changes_returns_recent_changes(self) -> None:
        # Given - create a book and a change log
        book = Book(
            name="Test Book",
            category="Fiction",
            price_excl_tax=10.0,
            price_incl_tax=12.0,
            availability="In stock",
            rating=4,
            image_url="http://example.com/test.jpg",
            source_url="http://example.com/test",
            content_hash="test_hash",
        )
        await self.book_repo.create(book)

        await self.change_log_repo.create(
            book_id=str(book.id),
            book_name=book.name,
            change_type="new_book",
            new_value=book.name,
        )

        # When
        result = await self.service.list_changes(page=1, page_size=10)

        # Then
        assert result.total == 1
        assert len(result.changes) == 1
        assert result.changes[0].change_type == "new_book"
        assert result.changes[0].book_name == "Test Book"
