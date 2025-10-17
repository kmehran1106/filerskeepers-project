import pytest
from httpx import AsyncClient

from filerskeepers.auth.models import User
from filerskeepers.auth.repositories import UserRepository
from filerskeepers.books.models import Book
from filerskeepers.books.repositories import BookRepository
from tests.base import TestBase


class TestBooksAPI(TestBase):
    @pytest.fixture(autouse=True)
    async def setup(
        self,
        user_repository: UserRepository,
        book_repository: BookRepository,
        cleanup: None,
    ) -> None:
        self.user_repo = user_repository
        self.book_repo = book_repository

        # Create a test user and get API key
        hashed_password = User.hash_password("testpassword")
        api_key = User.generate_api_key()
        self.user = await self.user_repo.create(
            email="test@example.com",
            hashed_password=hashed_password,
            api_key=api_key,
        )
        self.api_key = api_key

    @pytest.mark.anyio
    async def test_list_books_requires_authentication(
        self, client: AsyncClient
    ) -> None:
        # When
        response = await client.get("/books/v1")

        # Then
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_list_books_returns_paginated_results(
        self, client: AsyncClient
    ) -> None:
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
            content_hash="test_hash",
        )
        await self.book_repo.create(book)

        # When
        response = await client.get(
            "/books/v1",
            headers={"X-API-Key": self.api_key},
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["books"]) == 1
        assert data["books"][0]["name"] == "Test Book"
        assert data["page"] == 1
