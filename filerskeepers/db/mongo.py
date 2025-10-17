from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from filerskeepers.application.settings import Settings
from filerskeepers.auth.models import User
from filerskeepers.books.models import Book, ChangeLog
from filerskeepers.crawler.models import CrawlMetadata


async def init_mongo(settings: Settings) -> AsyncIOMotorClient[Any]:
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client.get_database(settings.MONGODB_DATABASE)

    # Initialize Beanie with document models
    # After this, User.find(), User.insert(), etc. work directly
    await init_beanie(
        database=database,  # type: ignore[arg-type]
        document_models=[User, Book, ChangeLog, CrawlMetadata],
    )

    return client
