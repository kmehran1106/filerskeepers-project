import asyncio
import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import redis.asyncio as redis
from arq.connections import ArqRedis, RedisSettings, create_pool
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from filerskeepers.application.rate_limiting import RateLimitMiddleware
from filerskeepers.application.settings import Settings
from filerskeepers.db.mongo import init_mongo
from filerskeepers.db.redis import get_redis_connection, get_redis_pool
from filerskeepers.queue.arq import get_arq_redis
from filerskeepers.queue.base import TaskContext, WorkerContext
from filerskeepers.web.auth import auth_router
from filerskeepers.web.ping import ping_router


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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def test_settings(
    mongodb_container: dict[str, str], redis_container: dict[str, str]
) -> Settings:
    return Settings(
        MONGODB_URL=mongodb_container["url"],
        MONGODB_DATABASE="test_filerskeepers",
        REDIS_URL=redis_container["url"],
        ENVIRONMENT="dev",
        DEBUG=True,
    )


@pytest.fixture(scope="session")
async def mongo_client(
    test_settings: Settings,
) -> AsyncGenerator[AsyncIOMotorClient[Any]]:
    client = await init_mongo(test_settings)
    yield client
    client.close()


@pytest.fixture
def fastapi_app() -> FastAPI:
    # Create app without lifespan
    app = FastAPI(
        title="FilersKeepers API",
        description="API for monitoring and serving e-commerce product data",
        version="0.1.0",
    )

    # Add middleware (will get Redis client from app.state during requests)
    app.add_middleware(RateLimitMiddleware)

    # Register routers
    app.include_router(auth_router, prefix="/auth/v1", tags=["Auth"])
    app.include_router(ping_router, prefix="/ping/v1", tags=["Ping"])

    return app


@pytest.fixture
async def override_dependencies(
    test_settings: Settings,
    redis_pool: redis.ConnectionPool,
    arq_redis: ArqRedis,
    mongo_client: AsyncIOMotorClient[Any],
    fastapi_app: FastAPI,
) -> AsyncGenerator[None]:
    # Set up app state for middleware and dependencies
    fastapi_app.state.redis_pool = redis_pool
    fastapi_app.state.redis_client = get_redis_connection(redis_pool)
    fastapi_app.state.mongo_client = mongo_client

    # Apply dependency overrides
    fastapi_app.dependency_overrides[get_redis_pool] = lambda: redis_pool
    fastapi_app.dependency_overrides[get_arq_redis] = lambda: arq_redis

    yield

    # Clear overrides and state
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
    mongo_client: AsyncIOMotorClient[Any],
    test_settings: Settings,
) -> AsyncGenerator[None]:
    # Clean up before test (in case previous test failed)
    db = mongo_client[test_settings.MONGODB_DATABASE]
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})

    yield

    # Clean up after test
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})
