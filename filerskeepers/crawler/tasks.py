from typing import Any

from loguru import logger

from filerskeepers.crawler.models import CrawlMetadata, CrawlStatus
from filerskeepers.queue.base import TaskContext, WorkerContext


async def crawl_books_task(ctx: WorkerContext) -> dict[str, Any]:
    async with TaskContext(ctx) as task_ctx:
        incomplete_crawl = (
            await task_ctx.crawl_metadata_repo.get_latest_incomplete_today()
        )

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
                url=task_ctx.crawler_service.BASE_URL,
                status=CrawlStatus.IN_PROGRESS,
            )
            await task_ctx.crawl_metadata_repo.create(metadata)

        try:
            books_found = metadata.books_crawled
            enqueued_count = 0
            errors: list[str] = list(metadata.error_messages)
            last_page = metadata.last_page_crawled

            # Use crawler service to fetch books (generator with resumable support)
            async for book_dto, page_num in task_ctx.crawler_service.crawl_all_books(
                start_page, crawl_id=str(metadata.id)
            ):
                books_found += 1
                try:
                    # Enqueue processing task with the DTO as dict
                    await task_ctx.arq_redis.enqueue_job(
                        "process_crawled_book", book_dto.model_dump()
                    )
                    enqueued_count += 1
                except Exception as e:
                    error_msg = f"Failed to enqueue book '{book_dto.name}': {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

                # Update checkpoint if we've moved to a new page
                if page_num > last_page:
                    last_page = page_num
                    metadata.last_page_crawled = last_page
                    metadata.books_crawled = books_found
                    metadata.errors_count = len(errors)
                    metadata.error_messages = errors[:100]
                    await task_ctx.crawl_metadata_repo.update(metadata)
                    logger.info(f"Checkpoint: Completed page {last_page}")

            # Mark crawl as complete
            if not errors:
                metadata.status = CrawlStatus.SUCCESS
            elif books_found > 0:
                metadata.status = CrawlStatus.PARTIAL
            else:
                metadata.status = CrawlStatus.FAILED

            status = metadata.status
            metadata.is_complete = True
            metadata.books_crawled = books_found
            metadata.errors_count = len(errors)
            metadata.error_messages = errors[:100]
            await task_ctx.crawl_metadata_repo.update(metadata)

            logger.info(
                f"Crawl completed: {books_found} books found, "
                f"{enqueued_count} enqueued for processing, "
                f"{len(errors)} errors, last page: {last_page}"
            )

            return {
                "status": "completed",
                "crawl_status": status,
                "books_found": books_found,
                "books_enqueued": enqueued_count,
                "errors_count": len(errors),
                "last_page": last_page,
                "resumed": incomplete_crawl is not None,
            }

        except Exception as e:
            logger.error(f"Error in scheduled book crawl: {e}")
            metadata.status = CrawlStatus.FAILED
            metadata.error_messages.append(f"Fatal error: {str(e)}")
            await task_ctx.crawl_metadata_repo.update(metadata)
            return {"status": "failed", "error": str(e)}
