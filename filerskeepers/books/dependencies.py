from typing import Annotated

from fastapi import Depends

from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.books.services import BookService


def get_book_repository() -> BookRepository:
    return BookRepository()


def get_change_log_repository() -> ChangeLogRepository:
    return ChangeLogRepository()


def get_book_service(
    book_repo: Annotated[BookRepository, Depends(get_book_repository)],
    change_log_repo: Annotated[ChangeLogRepository, Depends(get_change_log_repository)],
) -> BookService:
    return BookService(
        book_repo=book_repo,
        change_log_repo=change_log_repo,
    )
