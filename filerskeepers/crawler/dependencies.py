from filerskeepers.crawler.repositories import CrawlMetadataRepository
from filerskeepers.crawler.services import CrawlerService


def get_crawl_metadata_repository() -> CrawlMetadataRepository:
    return CrawlMetadataRepository()


def get_crawler_service() -> CrawlerService:
    return CrawlerService()
