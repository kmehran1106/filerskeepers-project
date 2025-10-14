from typing import Any

from arq.connections import RedisSettings
from arq.cron import cron
from loguru import logger

from filerskeepers.application.settings import settings
from filerskeepers.db.redis import get_redis_pool
from filerskeepers.queue.arq import get_arq_vars
from filerskeepers.queue.base import TaskContext, WorkerContext


async def startup(ctx: WorkerContext) -> None:
    try:
        ctx["redis_pool"] = get_redis_pool(settings)
    except Exception as e:
        logger.error(f"Failed to initialize repositories: {str(e)}")


async def shutdown(ctx: WorkerContext) -> None:
    try:
        await ctx["redis_pool"].aclose()
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
    ]
    cron_jobs = [
        cron(example_task, hour=2, minute=0),  # every day at 2:00 AM
        cron(example_task, minute=None),  # every minute
    ]
    verbose = True
    max_jobs = 10
    job_timeout = 300
    handle_signals = False
    log_results = True
