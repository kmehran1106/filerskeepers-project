from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron
from loguru import logger

from filerskeepers.application.settings import settings
from filerskeepers.books.tasks import process_crawled_book
from filerskeepers.crawler.tasks import crawl_books_task
from filerskeepers.db.mongo import init_mongo
from filerskeepers.db.redis import get_redis_pool
from filerskeepers.queue.arq import get_arq_vars
from filerskeepers.queue.base import TaskContext, WorkerContext


async def startup(ctx: WorkerContext) -> None:
    try:
        # Initialize Redis
        ctx["redis_pool"] = get_redis_pool(settings)

        # Initialize MongoDB
        ctx["mongo_client"] = await init_mongo(settings)
        logger.info("Initialized MongoDB and Beanie for ARQ worker")
    except Exception as e:
        logger.error(f"Failed to initialize repositories: {str(e)}")


async def shutdown(ctx: WorkerContext) -> None:
    try:
        await ctx["redis_pool"].aclose()
        if "mongo_client" in ctx:
            ctx["mongo_client"].close()
    except Exception as e:
        logger.error(f"Failed to close repositories: {str(e)}")


async def example_task(ctx: WorkerContext) -> dict[str, Any]:
    async with TaskContext(ctx):
        return {"status": "completed"}


class WorkerSettings:
    _host, _port, _db = get_arq_vars(settings.REDIS_URL)
    redis_settings: RedisSettings = RedisSettings(host=_host, port=_port, database=_db)
    on_startup = startup
    on_shutdown = shutdown
    functions = [
        example_task,
        crawl_books_task,
        process_crawled_book,
    ]
    cron_jobs = [
        cron(crawl_books_task, hour=2, minute=0),  # Daily crawl at 2:00 AM
    ]
    verbose = True
    max_jobs = 10
    job_timeout = 300
    handle_signals = False
    log_results = True
