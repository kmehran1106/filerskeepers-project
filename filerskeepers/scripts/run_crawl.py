import asyncio

from loguru import logger

from filerskeepers.application.settings import settings
from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.books.services import BookService
from filerskeepers.crawler.models import CrawlMetadata, CrawlStatus
from filerskeepers.crawler.repositories import CrawlMetadataRepository
from filerskeepers.crawler.services import CrawlerService
from filerskeepers.db.mongo import init_mongo


async def main() -> None:
    logger.info("Initializing database connection...")
    await init_mongo(settings)

    logger.info("Initializing dependencies...")
    crawl_metadata_repo = CrawlMetadataRepository()
    crawler_service = CrawlerService()
    book_service = BookService(
        book_repo=BookRepository(),
        change_log_repo=ChangeLogRepository(),
    )

    # Check for incomplete crawl
    incomplete_crawl = await crawl_metadata_repo.get_latest_incomplete_today()
    if incomplete_crawl:
        start_page = incomplete_crawl.last_page_crawled + 1
        logger.info(
            f"Resuming incomplete crawl from page {start_page} "
            f"(last crawled: {incomplete_crawl.last_page_crawled})"
        )
        metadata = incomplete_crawl
    else:
        start_page = 1
        logger.info("Starting new crawl from page 1")
        metadata = CrawlMetadata(
            url=crawler_service.BASE_URL,
            status=CrawlStatus.IN_PROGRESS,
        )
        await crawl_metadata_repo.create(metadata)

    logger.info(f"Starting crawl from {crawler_service.BASE_URL}")
    books_crawled = metadata.books_crawled
    books_processed = 0
    errors: list[str] = list(metadata.error_messages)
    last_page = metadata.last_page_crawled

    try:
        async for book_dto, page_num in crawler_service.crawl_all_books(
            start_page=start_page, crawl_id=str(metadata.id)
        ):
            books_crawled += 1
            logger.info(
                f"[Page {page_num}] Crawled book #{books_crawled}: {book_dto.name}"
            )

            # Process the book immediately
            try:
                result = await book_service.process_crawled_book(book_dto)
                books_processed += 1
                status = result.get("status")
                logger.info(f"Processed book '{book_dto.name}': status={status}")
            except Exception as e:
                error_msg = f"Failed to process book '{book_dto.name}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            # Update checkpoint if we've moved to a new page
            if page_num > last_page:
                last_page = page_num
                metadata.last_page_crawled = last_page
                metadata.books_crawled = books_crawled
                metadata.errors_count = len(errors)
                metadata.error_messages = errors[:100]
                await crawl_metadata_repo.update(metadata)
                logger.info(f"Checkpoint: Completed page {last_page}")

        # Mark crawl as complete
        if not errors:
            metadata.status = CrawlStatus.SUCCESS
        elif books_crawled > 0:
            metadata.status = CrawlStatus.PARTIAL
        else:
            metadata.status = CrawlStatus.FAILED

        metadata.is_complete = True
        metadata.books_crawled = books_crawled
        metadata.errors_count = len(errors)
        metadata.error_messages = errors[:100]
        await crawl_metadata_repo.update(metadata)

        logger.info(
            f"Crawl completed successfully. "
            f"Total books crawled: {books_crawled}, "
            f"processed: {books_processed}, "
            f"errors: {len(errors)}, "
            f"status: {metadata.status}"
        )

    except Exception as e:
        logger.error(f"Error during crawl: {e}")
        metadata.status = CrawlStatus.FAILED
        metadata.error_messages.append(f"Fatal error: {str(e)}")
        await crawl_metadata_repo.update(metadata)
        raise


if __name__ == "__main__":
    asyncio.run(main())
