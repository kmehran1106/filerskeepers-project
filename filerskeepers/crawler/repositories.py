from datetime import UTC, datetime, timedelta

from filerskeepers.crawler.models import CrawlMetadata, CrawlStatus, FailedParse


class CrawlMetadataRepository:
    async def create(self, metadata: CrawlMetadata) -> CrawlMetadata:
        await metadata.insert()
        return metadata

    async def update(self, metadata: CrawlMetadata) -> CrawlMetadata:
        await metadata.save()
        return metadata

    async def get_latest(self) -> CrawlMetadata | None:
        return await CrawlMetadata.find().sort("-timestamp").first_or_none()

    async def get_latest_incomplete_today(self) -> CrawlMetadata | None:
        today_start = datetime.now(UTC) - timedelta(hours=24)
        return (
            await CrawlMetadata.find(
                {
                    "timestamp": {"$gte": today_start},
                    "is_complete": False,
                    "status": {"$in": [CrawlStatus.IN_PROGRESS, CrawlStatus.PARTIAL]},
                }
            )
            .sort("-timestamp")
            .first_or_none()
        )


class FailedParseRepository:
    async def create(self, failed_parse: FailedParse) -> FailedParse:
        await failed_parse.insert()
        return failed_parse
