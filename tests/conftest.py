import asyncio
import logging
from collections.abc import AsyncGenerator, Generator

import pytest
import redis.asyncio as redis
from arq.connections import ArqRedis, RedisSettings, create_pool
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from filerskeepers.application.app import get_app
from filerskeepers.application.settings import Settings
from filerskeepers.db.redis import get_redis_connection, get_redis_pool
from filerskeepers.queue.arq import get_arq_redis
from filerskeepers.queue.base import TaskContext, WorkerContext


# Suppress noisy logs during tests
logging.getLogger("testcontainers").setLevel(logging.ERROR)
logging.getLogger("testcontainers.core.container").setLevel(logging.ERROR)
logging.getLogger("testcontainers.core.waiting_utils").setLevel(logging.ERROR)
logging.getLogger("docker").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("fastapi").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[dict[str, str]]:
    container = MongoDbContainer("mongo:8-noble")
    container.start()

    yield {
        "url": container.get_connection_url(),
        "host": container.get_container_host_ip(),
        "port": container.get_exposed_port(27017),
    }
    container.stop()


@pytest.fixture(scope="session")
def redis_container() -> Generator[dict[str, str]]:
    container = RedisContainer("redis:8.2-alpine")
    container.start()

    yield {
        "url": f"redis://{container.get_container_host_ip()}:{container.get_exposed_port(6379)}",
        "host": container.get_container_host_ip(),
        "port": container.get_exposed_port(6379),
    }
    container.stop()


@pytest.fixture(scope="session")
async def redis_pool(
    redis_container: dict[str, str],
) -> AsyncGenerator[redis.ConnectionPool]:
    pool = redis.ConnectionPool.from_url(redis_container["url"], max_connections=10)
    yield pool
    await pool.aclose()


@pytest.fixture
async def arq_redis(
    redis_container: dict[str, str],
) -> AsyncGenerator[ArqRedis]:
    arq_pool = await create_pool(
        RedisSettings(
            host=redis_container["host"],
            port=int(redis_container["port"]),
        )
    )
    yield arq_pool
    await arq_pool.aclose()


@pytest.fixture
async def test_settings(
    mongodb_container: dict[str, str], redis_container: dict[str, str]
) -> Settings:
    return Settings(
        MONGODB_URL=mongodb_container["url"],
        MONGODB_DATABASE="test_filerskeepers",
        REDIS_URL=redis_container["url"],
        ENVIRONMENT="dev",
        DEBUG=True,
    )


@pytest.fixture
def fastapi_app() -> FastAPI:
    return get_app()


@pytest.fixture
async def override_dependencies(
    test_settings: Settings,
    redis_pool: redis.ConnectionPool,
    arq_redis: ArqRedis,
    fastapi_app: FastAPI,
) -> AsyncGenerator[None]:
    # Apply overrides
    fastapi_app.dependency_overrides[get_redis_pool] = lambda: redis_pool
    fastapi_app.dependency_overrides[get_arq_redis] = lambda: arq_redis

    yield

    # Clear overrides
    fastapi_app.dependency_overrides.pop(get_redis_pool, None)
    fastapi_app.dependency_overrides.pop(get_arq_redis, None)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def client(
    fastapi_app: FastAPI,
    override_dependencies: None,
) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def redis_connection(redis_pool: redis.ConnectionPool) -> redis.Redis:
    return get_redis_connection(redis_pool)


@pytest.fixture
async def worker_context(
    redis_pool: redis.ConnectionPool,
    arq_redis: ArqRedis,
) -> WorkerContext:
    return {
        "redis_pool": redis_pool,
        "redis": arq_redis,
    }


@pytest.fixture
async def task_context(
    worker_context: WorkerContext,
) -> AsyncGenerator[TaskContext]:
    async with TaskContext(worker_context) as ctx:
        yield ctx


@pytest.fixture
async def cleanup(

) -> AsyncGenerator[None]:
    try:
        yield
    finally:
        pass
