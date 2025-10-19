import asyncio

from loguru import logger

from filerskeepers.application.settings import settings
from filerskeepers.crawler.repositories import CrawlMetadataRepository
from filerskeepers.crawler.services import CrawlerService
from filerskeepers.db.mongo import init_mongo


async def main() -> None:
    """Run the crawl directly in this process."""
    logger.info("Initializing database connection...")
    await init_mongo(settings)

    logger.info("Initializing dependencies...")
    _ = CrawlMetadataRepository()
    crawler_service = CrawlerService()

    logger.info(f"Starting crawl from {crawler_service.BASE_URL}")
    total_books = 0

    try:
        async for book_dto, page_num in crawler_service.crawl_all_books(start_page=1):
            total_books += 1
            logger.info(
                f"[Page {page_num}] Crawled book #{total_books}: {book_dto.name}"
            )

        logger.info(f"Crawl completed successfully. Total books crawled: {total_books}")

    except Exception as e:
        logger.error(f"Error during crawl: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
