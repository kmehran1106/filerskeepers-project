import asyncio
from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from filerskeepers.application.settings import settings
from filerskeepers.crawler.dtos import CrawledBookDto
from filerskeepers.crawler.models import FailedParse
from filerskeepers.crawler.parser import BookParser
from filerskeepers.crawler.repositories import FailedParseRepository


class CrawlerService:
    BASE_URL = "https://books.toscrape.com"
    CATALOG_URL = f"{BASE_URL}/catalogue/page-{{page}}.html"

    def __init__(
        self, failed_parse_repo: FailedParseRepository = FailedParseRepository()
    ) -> None:
        self.parser = BookParser()
        self.timeout = settings.CRAWLER_TIMEOUT
        self.max_retries = settings.CRAWLER_MAX_RETRIES
        self.retry_delay = settings.CRAWLER_RETRY_DELAY
        self.failed_parse_repo = failed_parse_repo

    async def crawl_all_books(
        self, start_page: int = 1, crawl_id: str | None = None
    ) -> AsyncGenerator[tuple[CrawledBookDto, int]]:
        logger.info(f"Starting crawl from page {start_page}")
        page = start_page

        while True:
            try:
                catalog_url = (
                    self.CATALOG_URL.format(page=page)
                    if page > 1
                    else f"{self.BASE_URL}/index.html"
                )
                logger.info(f"Crawling catalog page {page}: {catalog_url}")

                html = await self._fetch_with_retry(catalog_url)
                if not html:
                    logger.warning(f"Failed to fetch catalog page {page}")
                    break

                # Extract book URLs from this page
                book_urls = self.parser.parse_catalog_page(html, self.BASE_URL)
                logger.info(f"Found {len(book_urls)} books on page {page}")

                # Crawl books from this page and yield them with page number
                async for book_dto in self._crawl_books_batch(book_urls, crawl_id):
                    yield book_dto, page

                # Check if there's a next page
                next_page = self.parser.has_next_page(html)
                if not next_page:
                    logger.info(f"No more pages after page {page}")
                    break

                page += 1
            except Exception as e:
                logger.error(f"Error crawling catalog page {page}: {e}")
                break

        logger.info(f"Crawl completed at page {page}")

    async def crawl_book(
        self, url: str, crawl_id: str | None = None
    ) -> CrawledBookDto | None:
        try:
            html = await self._fetch_with_retry(url)
            if not html:
                logger.warning(f"Failed to fetch book page: {url}")
                # Store failed fetch attempt
                failed_parse = FailedParse(
                    crawl_id=crawl_id,
                    url=url,
                    html=None,
                    failure_reason="Failed to fetch HTML from server",
                )
                await self.failed_parse_repo.create(failed_parse)
                return None

            book_data = self.parser.parse_book_page(html, url)
            if not book_data:
                logger.warning(f"Failed to parse book page: {url}")
                # Store failed parse attempt with HTML
                failed_parse = FailedParse(
                    crawl_id=crawl_id,
                    url=url,
                    html=html,
                    failure_reason="Failed to parse book data from HTML",
                )
                await self.failed_parse_repo.create(failed_parse)
                return None

            return CrawledBookDto(**book_data, crawl_id=crawl_id)
        except Exception as e:
            logger.error(f"Error crawling book {url}: {e}")
            return None

    async def _crawl_books_batch(
        self, urls: list[str], crawl_id: str | None = None
    ) -> AsyncGenerator[CrawledBookDto]:
        batch_size = 10  # Process 10 books concurrently

        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            total_batches = (len(urls) + batch_size - 1) // batch_size
            logger.info(f"Processing batch {i // batch_size + 1}/{total_batches}")

            # Crawl books in this batch concurrently
            tasks = [self.crawl_book(url, crawl_id) for url in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and yield successful ones
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    error_msg = f"Exception crawling {url}: {result}"
                    logger.error(error_msg)
                elif isinstance(result, CrawledBookDto):
                    yield result
                elif result is None:
                    logger.warning(f"Failed to crawl {url}")

            # Small delay between batches to be nice to the server
            await asyncio.sleep(0.5)

    async def _fetch_with_retry(self, url: str) -> str | None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text

                except httpx.HTTPStatusError as e:
                    if e.response.status_code >= 500:
                        # Server error - retry with backoff
                        wait_time = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"Server error {e.response.status_code} for {url}, "
                            f"retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        # Client error - don't retry
                        logger.error(f"Client error {e.response.status_code} for {url}")
                        return None

                except (httpx.RequestError, httpx.TimeoutException) as e:
                    # Network error or timeout - retry with backoff
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Request error for {url}: {e}, "
                        f"retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)

                except Exception as e:
                    logger.error(f"Unexpected error fetching {url}: {e}")
                    return None

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
