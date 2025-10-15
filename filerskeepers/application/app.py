from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from filerskeepers.application.logging import setup_logging
from filerskeepers.application.rate_limiting import RateLimitMiddleware
from filerskeepers.application.settings import settings
from filerskeepers.db.mongo import init_mongo
from filerskeepers.db.redis import get_redis_connection, get_redis_pool
from filerskeepers.web.auth import auth_router
from filerskeepers.web.ping import ping_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    logger.info("Starting application...")

    # Initialize MongoDB and Beanie
    mongo_client: AsyncIOMotorClient[Any] = await init_mongo(settings)
    app.state.mongo_client = mongo_client
    logger.info("MongoDB and Beanie initialized")

    # Initialize Redis
    redis_pool = get_redis_pool(settings)
    app.state.redis_pool = redis_pool

    # Create Redis client for rate limiting middleware
    redis_client = get_redis_connection(redis_pool)
    app.state.redis_client = redis_client

    logger.info("Redis pool and client initialized")

    yield

    # Cleanup
    logger.info("Shutting down application...")
    await redis_pool.aclose()
    mongo_client.close()
    logger.info("Application shut down complete")


def get_app() -> FastAPI:
    app = FastAPI(
        title="FilersKeepers API",
        description="API for monitoring and serving e-commerce product data",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add middleware (will get Redis client from app.state during requests)
    app.add_middleware(RateLimitMiddleware)

    # Register routers
    app.include_router(auth_router, prefix="/auth/v1", tags=["Auth"])
    app.include_router(ping_router, prefix="/ping/v1", tags=["Ping"])

    return app
