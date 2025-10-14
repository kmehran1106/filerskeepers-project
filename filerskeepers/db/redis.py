import redis.asyncio as redis

from filerskeepers.application.settings import Settings


_REDIS_POOL: redis.ConnectionPool | None = None


def get_redis_pool(
    settings: Settings, max_connections: int = 10
) -> redis.ConnectionPool:
    global _REDIS_POOL
    if _REDIS_POOL is None:
        _REDIS_POOL = redis.ConnectionPool.from_url(
            settings.REDIS_URL, max_connections=max_connections
        )
    return _REDIS_POOL


def get_redis_connection(pool: redis.ConnectionPool) -> redis.Redis:
    return redis.Redis(connection_pool=pool)
