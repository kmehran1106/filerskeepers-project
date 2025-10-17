import hashlib
import re
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger


class BookParser:
    RATING_MAP = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }

    def parse_book_page(self, html: str, url: str) -> dict[str, Any] | None:
        try:
            soup = BeautifulSoup(html, "html.parser")

            name = self._extract_name(soup)
            if not name:
                logger.warning(f"Failed to extract book name from {url}")
                return None

            data = {
                "name": name,
                "description": self._extract_description(soup),
                "category": self._extract_category(soup),
                "price_excl_tax": self._extract_price_excl_tax(soup),
                "price_incl_tax": self._extract_price_incl_tax(soup),
                "availability": self._extract_availability(soup),
                "num_reviews": self._extract_num_reviews(soup),
                "image_url": self._extract_image_url(soup, url),
                "rating": self._extract_rating(soup),
                "source_url": url,
                "html_snapshot": html,
            }

            data["content_hash"] = self._generate_content_hash(data)

            return data

        except Exception as e:
            logger.error(f"Error parsing book page {url}: {e}")
            return None

    def parse_catalog_page(self, html: str, base_url: str) -> list[str]:
        try:
            soup = BeautifulSoup(html, "html.parser")
            book_urls = []

            articles = soup.find_all("article", class_="product_pod")

            for article in articles:
                h3 = article.find("h3")
                if h3:
                    a = h3.find("a")
                    if a:
                        href = a.get("href")
                        if href and isinstance(href, str):
                            # Construct absolute URL
                            relative_url = href
                            # Remove leading '../' or './'
                            relative_url = relative_url.replace("../", "").replace(
                                "./", ""
                            )
                            absolute_url = f"{base_url}/catalogue/{relative_url}"
                            book_urls.append(absolute_url)

            return book_urls

        except Exception as e:
            logger.error(f"Error parsing catalog page: {e}")
            return []

    def has_next_page(self, html: str) -> str | None:
        try:
            soup = BeautifulSoup(html, "html.parser")
            next_link = soup.find("li", class_="next")

            if next_link:
                a = next_link.find("a")
                if a:
                    href = a.get("href")
                    if href and isinstance(href, str):
                        return href

            return None

        except Exception as e:
            logger.error(f"Error checking for next page: {e}")
            return None

    def _extract_name(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        return h1.text.strip() if h1 else ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc_header = soup.find("div", id="product_description")
        if desc_header:
            p = desc_header.find_next_sibling("p")
            if p:
                return p.text.strip()
        return ""

    def _extract_category(self, soup: BeautifulSoup) -> str:
        breadcrumb = soup.find("ul", class_="breadcrumb")
        if breadcrumb:
            links = breadcrumb.find_all("a")
            if len(links) >= 2:
                return links[-1].text.strip()
        return "Unknown"

    def _extract_price_excl_tax(self, soup: BeautifulSoup) -> float:
        return self._extract_price_from_table(soup, "Price (excl. tax)")

    def _extract_price_incl_tax(self, soup: BeautifulSoup) -> float:
        return self._extract_price_from_table(soup, "Price (incl. tax)")

    def _extract_price_from_table(self, soup: BeautifulSoup, label: str) -> float:
        table = soup.find("table", class_="table-striped")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td and th.text.strip() == label:
                    # Extract numeric value from price string (e.g., "£51.77")
                    price_text = td.text.strip()
                    match = re.search(r"[\d.]+", price_text)
                    if match:
                        return float(match.group())
        return 0.0

    def _extract_availability(self, soup: BeautifulSoup) -> str:
        avail = soup.find("p", class_="instock availability")
        if avail:
            text = avail.text.strip()
            # Extract the actual availability text (e.g., "In stock (22 available)")
            return " ".join(text.split())
        return "Unknown"

    def _extract_num_reviews(self, soup: BeautifulSoup) -> int:
        table = soup.find("table", class_="table-striped")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td and th.text.strip() == "Number of reviews":
                    try:
                        return int(td.text.strip())
                    except ValueError:
                        return 0
        return 0

    def _extract_image_url(self, soup: BeautifulSoup, page_url: str) -> str:
        img = soup.find("div", class_="item active")
        if img:
            img_tag = img.find("img")
            if img_tag:
                src = img_tag.get("src")
                if src and isinstance(src, str):
                    # Construct absolute URL
                    relative_url = src
                    # Remove leading '../' or './'
                    relative_url = relative_url.replace("../", "").replace("./", "")
                    # Get base URL from page_url
                    base_url = "/".join(page_url.split("/")[:3])
                    return f"{base_url}/{relative_url}"
        return ""

    def _extract_rating(self, soup: BeautifulSoup) -> int:
        rating_p = soup.find("p", class_="star-rating")
        if rating_p:
            # Rating is in the class name (e.g., "star-rating Three")
            classes_attr = rating_p.get("class")
            if classes_attr:
                classes = (
                    classes_attr if isinstance(classes_attr, list) else [classes_attr]
                )
                for cls in classes:
                    if isinstance(cls, str) and cls in self.RATING_MAP:
                        return self.RATING_MAP[cls]
        return 0

    def _generate_content_hash(self, data: dict[str, Any]) -> str:
        content = (
            f"{data['name']}|"
            f"{data['price_excl_tax']}|"
            f"{data['price_incl_tax']}|"
            f"{data['availability']}|"
            f"{data['num_reviews']}"
        )
        return hashlib.sha256(content.encode()).hexdigest()
