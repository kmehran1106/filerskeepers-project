from datetime import datetime
from typing import Self

from pydantic import BaseModel

from filerskeepers.books.models import Book, ChangeLog


class BookResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price_excl_tax: float
    price_incl_tax: float
    availability: str
    num_reviews: int
    image_url: str
    rating: int
    source_url: str
    crawl_timestamp: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_object(cls, book: Book) -> Self:
        return cls(
            id=str(book.id),
            name=book.name,
            description=book.description,
            category=book.category,
            price_excl_tax=book.price_excl_tax,
            price_incl_tax=book.price_incl_tax,
            availability=book.availability,
            num_reviews=book.num_reviews,
            image_url=book.image_url,
            rating=book.rating,
            source_url=book.source_url,
            crawl_timestamp=book.crawl_timestamp,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )


class BookListResponse(BaseModel):
    books: list[BookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChangeLogResponse(BaseModel):
    id: str
    book_id: str
    book_name: str
    change_type: str
    old_value: str | None
    new_value: str | None
    field_changed: str | None
    timestamp: datetime

    @classmethod
    def from_object(cls, change: ChangeLog) -> Self:
        return cls(
            id=str(change.id),
            book_id=change.book_id,
            book_name=change.book_name,
            change_type=change.change_type,
            old_value=change.old_value,
            new_value=change.new_value,
            field_changed=change.field_changed,
            timestamp=change.timestamp,
        )


class ChangeLogListResponse(BaseModel):
    changes: list[ChangeLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
