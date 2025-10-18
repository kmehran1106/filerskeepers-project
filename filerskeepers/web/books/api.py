from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from filerskeepers.auth.dependencies import get_current_user
from filerskeepers.auth.models import User
from filerskeepers.books.dependencies import get_book_service
from filerskeepers.books.dtos import (
    BookListResponse,
    BookResponse,
    ChangeLogListResponse,
)
from filerskeepers.books.services import BookService


books_router = APIRouter(dependencies=[Depends(get_current_user)])


@books_router.get(
    "",
    response_model=BookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List books",
    description="Get a paginated list of books with optional filtering and sorting",
)
async def list_books(
    book_service: Annotated[BookService, Depends(get_book_service)],
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    min_price: Annotated[
        float | None, Query(description="Minimum price (inclusive)", ge=0)
    ] = None,
    max_price: Annotated[
        float | None, Query(description="Maximum price (inclusive)", ge=0)
    ] = None,
    rating: Annotated[
        int | None, Query(description="Filter by rating", ge=1, le=5)
    ] = None,
    sort_by: Annotated[
        Literal["rating", "price", "reviews"] | None,
        Query(description="Sort by field"),
    ] = None,
    page: Annotated[int, Query(description="Page number", ge=1)] = 1,
    page_size: Annotated[int, Query(description="Page size", ge=1, le=100)] = 10,
    current_user: User = Depends(get_current_user),
) -> BookListResponse:
    return await book_service.list_books(
        category=category,
        min_price=min_price,
        max_price=max_price,
        rating=rating,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@books_router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get book by ID",
    description="Get full details of a specific book",
)
async def get_book(
    book_id: str,
    book_service: Annotated[BookService, Depends(get_book_service)],
    current_user: User = Depends(get_current_user),
) -> BookResponse:
    book = await book_service.get_book(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found",
        )
    return book


@books_router.get(
    "/changes/report",
    status_code=status.HTTP_200_OK,
    summary="Generate change report",
    description=(
        "Generate a downloadable change report in JSON or CSV format for a "
        "specific date range (default: last 24 hours)"
    ),
)
async def generate_change_report(
    book_service: Annotated[BookService, Depends(get_book_service)],
    format_type: Annotated[
        Literal["json", "csv"], Query(alias="format", description="Report format")
    ] = "json",
    start_date: Annotated[
        datetime | None,
        Query(description="Start date (ISO format, default: 24 hours ago)"),
    ] = None,
    end_date: Annotated[
        datetime | None, Query(description="End date (ISO format, default: now)")
    ] = None,
    current_user: User = Depends(get_current_user),
) -> Response:
    report_content = await book_service.generate_change_report(
        start_date=start_date,
        end_date=end_date,
        format_type=format_type,
    )

    # Set appropriate content type and filename
    if format_type == "json":
        media_type = "application/json"
        filename = f"change_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        media_type = "text/csv"
        filename = f"change_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=report_content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@books_router.get(
    "/changes",
    response_model=ChangeLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List changes",
    description=("Get paginated list of recent changes"),
)
async def list_changes(
    book_service: Annotated[BookService, Depends(get_book_service)],
    book_id: Annotated[str | None, Query(description="Filter by book ID")] = None,
    change_type: Annotated[
        Literal["new_book", "price_change", "availability_change", "other"] | None,
        Query(description="Filter by change type"),
    ] = None,
    page: Annotated[int, Query(description="Page number", ge=1)] = 1,
    page_size: Annotated[int, Query(description="Page size", ge=1, le=100)] = 10,
    current_user: User = Depends(get_current_user),
) -> ChangeLogListResponse:
    return await book_service.list_changes(
        book_id=book_id,
        change_type=change_type,
        page=page,
        page_size=page_size,
    )
