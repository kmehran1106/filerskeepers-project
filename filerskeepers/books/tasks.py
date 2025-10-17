from typing import Any

from loguru import logger

from filerskeepers.crawler.dtos import CrawledBookDto
from filerskeepers.queue.base import TaskContext, WorkerContext


async def process_crawled_book(
    ctx: WorkerContext, book_data: dict[str, Any]
) -> dict[str, Any]:
    async with TaskContext(ctx) as task_ctx:
        try:
            # Reconstruct the DTO from the dict
            book_dto = CrawledBookDto(**book_data)

            result = await task_ctx.book_service.process_crawled_book(book_dto)

            status = result.get("status")
            logger.info(f"Processed book '{book_dto.name}': status={status}")

            return result
        except Exception as e:
            logger.error(f"Error in process_crawled_book task: {e}")
            return {"status": "error", "error": str(e)}
