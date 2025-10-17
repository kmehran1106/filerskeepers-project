from types import TracebackType
from typing import Any, TypeVar

import redis.asyncio as redis
from arq import ArqRedis
from loguru import logger

from filerskeepers.application.settings import Settings, settings
from filerskeepers.books.repositories import BookRepository, ChangeLogRepository
from filerskeepers.books.services import BookService
from filerskeepers.crawler.repositories import CrawlMetadataRepository
from filerskeepers.crawler.services import CrawlerService


WorkerContext = dict[str, Any]
T = TypeVar("T", bound="TaskContext")


class TaskContext:
    def __init__(self, ctx: WorkerContext) -> None:
        self._worker_ctx = ctx
        self.settings: Settings
        self.arq_redis: ArqRedis
        self.redis_pool: redis.ConnectionPool

    async def __aenter__(self: T) -> T:
        try:
            self.settings = settings

            self.arq_redis = self._worker_ctx["redis"]
            assert self.arq_redis is not None, "Failed to initialize arq redis"

            self.redis_pool = self._worker_ctx["redis_pool"]
            assert self.redis_pool is not None, "Failed to initialize redis pool"

            self.book_repo = BookRepository()
            self.change_log_repo = ChangeLogRepository()
            self.crawl_metadata_repo = CrawlMetadataRepository()

            self.crawler_service = CrawlerService()
            self.book_service = BookService(
                book_repo=self.book_repo,
                change_log_repo=self.change_log_repo,
            )

            return self
        except Exception as e:
            logger.error(f"Failed to initialize task context: {str(e)}")
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            # NOTE: cleanup resources if needed
            pass
        finally:
            if self.redis_pool:
                await self.redis_pool.disconnect()
