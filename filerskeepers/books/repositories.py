from typing import Literal

from filerskeepers.books.models import Book, ChangeLog


class BookRepository:
    async def create(self, book: Book) -> Book:
        await book.insert()
        return book

    async def find_by_id(self, book_id: str) -> Book | None:
        return await Book.get(book_id)

    async def find_by_content_hash(self, content_hash: str) -> Book | None:
        return await Book.find_one(Book.content_hash == content_hash)

    async def find_by_url(self, url: str) -> Book | None:
        return await Book.find_one(Book.source_url == url)

    async def list_books(
        self,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        rating: int | None = None,
        sort_by: Literal["rating", "price", "reviews"] | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[Book], int]:
        query = Book.find()

        if category:
            query = query.find(Book.category == category)

        if min_price is not None:
            query = query.find(Book.price_incl_tax >= min_price)

        if max_price is not None:
            query = query.find(Book.price_incl_tax <= max_price)

        if rating is not None:
            query = query.find(Book.rating == rating)

        total = await query.count()

        if sort_by == "rating":
            query = query.sort("-rating")
        elif sort_by == "price":
            query = query.sort("price_incl_tax")
        elif sort_by == "reviews":
            query = query.sort("-num_reviews")
        else:
            query = query.sort("-created_at")

        books = await query.skip(skip).limit(limit).to_list()

        return books, total

    async def update(self, book: Book) -> Book:
        book.update_timestamp()
        await book.save()
        return book

    async def bulk_create(self, books: list[Book]) -> list[Book]:
        await Book.insert_many(books)
        return books


class ChangeLogRepository:
    async def create(
        self,
        book_id: str,
        book_name: str,
        change_type: Literal[
            "new_book", "price_change", "availability_change", "other"
        ],
        old_value: str | None = None,
        new_value: str | None = None,
        field_changed: str | None = None,
        crawl_id: str | None = None,
    ) -> ChangeLog:
        change_log = ChangeLog(
            book_id=book_id,
            book_name=book_name,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            field_changed=field_changed,
            crawl_id=crawl_id,
        )
        await change_log.insert()
        return change_log

    async def list_changes(
        self,
        book_id: str | None = None,
        change_type: str | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[ChangeLog], int]:
        query = ChangeLog.find()

        if book_id:
            query = query.find(ChangeLog.book_id == book_id)

        if change_type:
            query = query.find(ChangeLog.change_type == change_type)

        total = await query.count()

        query = query.sort("-timestamp")

        changes = await query.skip(skip).limit(limit).to_list()

        return changes, total
