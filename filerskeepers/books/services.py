from typing import Literal

from loguru import logger

from filerskeepers.books.dtos import (
    BookListResponse,
    BookResponse,
    ChangeLogListResponse,
    ChangeLogResponse,
)
from filerskeepers.books.models import Book
from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.crawler.dtos import CrawledBookDto


class BookService:
    def __init__(
        self,
        book_repo: BookRepository,
        change_log_repo: ChangeLogRepository,
    ) -> None:
        self.book_repo = book_repo
        self.change_log_repo = change_log_repo

    async def process_crawled_book(
        self, book_dto: CrawledBookDto
    ) -> dict[str, str | bool]:
        try:
            # Check if book already exists by URL
            existing_book = await self.book_repo.find_by_url(book_dto.source_url)

            if existing_book:
                # Book exists - check for changes
                if existing_book.content_hash != book_dto.content_hash:
                    # Content has changed
                    await self._detect_and_log_changes(existing_book, book_dto)

                    # Update the book
                    book_dict = book_dto.model_dump()
                    for key, value in book_dict.items():
                        if key not in ["html_snapshot"]:  # Keep old snapshot
                            setattr(existing_book, key, value)

                    await self.book_repo.update(existing_book)
                    logger.info(f"Updated book: {book_dto.name}")
                    return {"status": "updated", "book_id": str(existing_book.id)}
                else:
                    # No changes
                    return {"status": "unchanged", "book_id": str(existing_book.id)}

            else:
                # New book - create it
                book = Book(**book_dto.model_dump())
                await self.book_repo.create(book)

                # Log as new book
                await self.change_log_repo.create(
                    book_id=str(book.id),
                    book_name=book.name,
                    change_type="new_book",
                    new_value=book.name,
                )
                logger.info(f"Created new book: {book_dto.name}")
                return {"status": "created", "book_id": str(book.id)}

        except Exception as e:
            logger.error(f"Error processing book {book_dto.name}: {e}")
            return {"status": "error", "error": str(e)}

    async def _detect_and_log_changes(
        self, existing_book: Book, new_data: CrawledBookDto
    ) -> None:
        book_id = str(existing_book.id)
        book_name = existing_book.name

        # Check price changes
        if existing_book.price_incl_tax != new_data.price_incl_tax:
            await self.change_log_repo.create(
                book_id=book_id,
                book_name=book_name,
                change_type="price_change",
                old_value=f"£{existing_book.price_incl_tax:.2f}",
                new_value=f"£{new_data.price_incl_tax:.2f}",
                field_changed="price_incl_tax",
            )
            logger.info(
                f"Price changed for {book_name}: "
                f"£{existing_book.price_incl_tax:.2f} -> "
                f"£{new_data.price_incl_tax:.2f}"
            )

        if existing_book.price_excl_tax != new_data.price_excl_tax:
            await self.change_log_repo.create(
                book_id=book_id,
                book_name=book_name,
                change_type="price_change",
                old_value=f"£{existing_book.price_excl_tax:.2f}",
                new_value=f"£{new_data.price_excl_tax:.2f}",
                field_changed="price_excl_tax",
            )

        # Check availability changes
        if existing_book.availability != new_data.availability:
            await self.change_log_repo.create(
                book_id=book_id,
                book_name=book_name,
                change_type="availability_change",
                old_value=existing_book.availability,
                new_value=new_data.availability,
                field_changed="availability",
            )
            logger.info(
                f"Availability changed for {book_name}: "
                f"{existing_book.availability} -> {new_data.availability}"
            )

        # Check for other changes (rating, reviews, etc.)
        if existing_book.rating != new_data.rating:
            await self.change_log_repo.create(
                book_id=book_id,
                book_name=book_name,
                change_type="other",
                old_value=str(existing_book.rating),
                new_value=str(new_data.rating),
                field_changed="rating",
            )

        if existing_book.num_reviews != new_data.num_reviews:
            await self.change_log_repo.create(
                book_id=book_id,
                book_name=book_name,
                change_type="other",
                old_value=str(existing_book.num_reviews),
                new_value=str(new_data.num_reviews),
                field_changed="num_reviews",
            )

    async def get_book(self, book_id: str) -> BookResponse | None:
        book = await self.book_repo.find_by_id(book_id)
        if not book:
            return None

        return BookResponse.from_object(book)

    async def list_books(
        self,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        rating: int | None = None,
        sort_by: Literal["rating", "price", "reviews"] | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> BookListResponse:
        skip = (page - 1) * page_size

        books, total = await self.book_repo.list_books(
            category=category,
            min_price=min_price,
            max_price=max_price,
            rating=rating,
            sort_by=sort_by,
            skip=skip,
            limit=page_size,
        )

        total_pages = (total + page_size - 1) // page_size

        return BookListResponse(
            books=[BookResponse.from_object(book) for book in books],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def list_changes(
        self,
        book_id: str | None = None,
        change_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ChangeLogListResponse:
        skip = (page - 1) * page_size

        changes, total = await self.change_log_repo.list_changes(
            book_id=book_id,
            change_type=change_type,
            skip=skip,
            limit=page_size,
        )

        total_pages = (total + page_size - 1) // page_size

        return ChangeLogListResponse(
            changes=[ChangeLogResponse.from_object(change) for change in changes],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
