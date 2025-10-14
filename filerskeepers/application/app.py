from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from filerskeepers.application.logging import setup_logging
from filerskeepers.application.rate_limiting import RateLimitMiddleware
from filerskeepers.application.settings import settings
from filerskeepers.db.redis import get_redis_connection, get_redis_pool
from filerskeepers.web.ping import ping_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger.info("Starting application...")

    # Initialize Redis
    redis_pool = get_redis_pool(settings)
    app.state.redis_pool = redis_pool

    logger.info("Redis pool initialized")

    yield

    # Cleanup
    logger.info("Shutting down application...")
    await redis_pool.aclose()
    logger.info("Application shut down complete")


def get_app() -> FastAPI:
    app = FastAPI(
        title="FilersKeepers API",
        description="API for monitoring and serving e-commerce product data",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Initialize Redis for rate limiting middleware
    redis_pool = get_redis_pool(settings, max_connections=3)
    redis_client = get_redis_connection(redis_pool)

    # Add middleware
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

    # Register routers
    app.include_router(ping_router, prefix="/ping/v1", tags=["Ping"])

    return app
