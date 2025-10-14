from urllib.parse import urlparse

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from filerskeepers.application.settings import Settings


_ARQ_REDIS: ArqRedis | None = None


def get_arq_vars(redis_url: str) -> tuple[str, int, int]:
    if not redis_url:
        raise ValueError("Redis URL cannot be empty")

    try:
        parsed = urlparse(redis_url)

        if parsed.scheme not in ("redis", "rediss"):
            raise ValueError(f"Invalid Redis URL scheme: {parsed.scheme}")

        # Extract host
        host = parsed.hostname or "localhost"

        # Extract port
        port = parsed.port or 6379

        # Extract db number from path
        db = int(parsed.path.lstrip("/") or "0")

        return host, port, db

    except Exception as e:
        raise ValueError(f"Failed to parse Redis URL: {e}")


async def get_arq_redis(settings: Settings) -> ArqRedis:
    global _ARQ_REDIS
    if _ARQ_REDIS is None:
        try:
            _host, _port, _db = get_arq_vars(settings.REDIS_URL)
            _ARQ_REDIS = await create_pool(
                RedisSettings(host=_host, port=_port, database=_db),
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")
    return _ARQ_REDIS
