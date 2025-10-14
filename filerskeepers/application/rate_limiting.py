from collections.abc import Awaitable, Callable
from time import time

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from filerskeepers.application.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        redis_client: redis.Redis,
        rate_limit: int = settings.RATE_LIMIT_PER_HOUR,
    ) -> None:
        super().__init__(app)
        self.rate_limit = rate_limit
        self.redis = redis_client
        self.window = 3600  # 1 hour in seconds

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return await call_next(request)

        key = f"rate_limit:{api_key}"
        current_time = int(time())
        window_start = current_time - self.window

        async with self.redis.pipeline() as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zcard(key)
            await pipe.zadd(key, {str(current_time): current_time})
            await pipe.expire(key, self.window)
            results = await pipe.execute()

        request_count = results[1]

        if request_count >= self.rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.rate_limit} requests/hour",
            )

        return await call_next(request)
