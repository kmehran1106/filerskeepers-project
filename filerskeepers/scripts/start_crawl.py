import asyncio

from arq import ArqRedis
from arq.jobs import Job

from filerskeepers.application.settings import settings
from filerskeepers.queue.arq import get_arq_redis


async def start_crawl() -> None:
    arq_redis: ArqRedis = await get_arq_redis(settings)

    try:
        job = await arq_redis.enqueue_job("crawl_books_task")
        assert isinstance(job, Job)
        print()
        print("✓ Crawl task enqueued successfully")
        print(f"  Job ID: {job.job_id}")
    except Exception as e:
        print(f"✗ Failed to enqueue crawl task: {e}")
        raise
    finally:
        await arq_redis.close()


if __name__ == "__main__":
    asyncio.run(start_crawl())
