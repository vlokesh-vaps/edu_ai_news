"""Fetch recent AI, AI-education, and Indian education news from RSS feeds."""

import calendar
import asyncio
import logging
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import httpx


logger = logging.getLogger(__name__)

HTTP_HEADERS = {
    "User-Agent": os.getenv(
        "FEED_USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        ),
    ),
    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
HTTP_TIMEOUT_SECONDS = 20.0
HTTP_RETRY_ATTEMPTS = 3


# The three feeds reflect the three supported content categories. Content is
# still validated locally because a search feed can return unrelated stories.
RSS_FEEDS: List[str] = [
    (
        "https://news.google.com/rss/search?"
        "q=(artificial+intelligence+OR+generative+AI+OR+machine+learning)+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
    (
        "https://news.google.com/rss/search?"
        "q=(%22AI+in+education%22+OR+%22education+AI%22+OR+EdTech)+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
    (
        "https://news.google.com/rss/search?"
        "q=India+(education+OR+schools+OR+universities)+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
]

AI_TERMS: Tuple[str, ...] = (
    "ai",
    "artificial intelligence",
    "generative ai",
    "genai",
    "machine learning",
    "large language model",
    "large language models",
    "llm",
    "llms",
    "chatgpt",
    "openai",
    "anthropic",
    "gemini",
    "copilot",
)

EDUCATION_TERMS: Tuple[str, ...] = (
    "education",
    "educational",
    "school",
    "schools",
    "student",
    "students",
    "teacher",
    "teachers",
    "teaching",
    "classroom",
    "classrooms",
    "college",
    "colleges",
    "university",
    "universities",
    "campus",
    "curriculum",
    "learning",
    "edtech",
    "higher education",
    "academic",
    "academics",
    "scholarship",
    "scholarships",
    "exam",
    "exams",
)

INDIA_TERMS: Tuple[str, ...] = (
    "india",
    "indian",
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
    "delhi",
    "chandigarh",
    "jammu",
    "kashmir",
    "ladakh",
    "puducherry",
    "mumbai",
    "bengaluru",
    "bangalore",
    "chennai",
    "kolkata",
    "hyderabad",
    "ahmedabad",
    "pune",
    "jaipur",
    "lucknow",
    "patna",
    "bhopal",
    "bhubaneswar",
    "kochi",
    "cbse",
    "icse",
    "ugc",
    "ncert",
    "neet",
    "jee",
    "iit",
    "iim",
    "nit",
    "cuet",
    "nta",
)

# Hardware-focused stories are outside this application's scope in every
# category, including AI education and Indian education.
HARDWARE_TERMS: Tuple[str, ...] = (
    "chip",
    "chips",
    "chipset",
    "semiconductor",
    "semiconductors",
    "gpu",
    "gpus",
    "processor",
    "processors",
    "data center",
    "data centers",
    "server",
    "servers",
    "smartphone",
    "smartphones",
    "laptop",
    "laptops",
    "robot",
    "robots",
    "robotics",
    "device",
    "devices",
)

NON_EDUCATION_PROFILE_PATTERNS: Tuple[str, ...] = (
    r"(?<!\w)built\s+(?:an?\s+)?(?:rs\.?\s*)?[\w\s-]*business(?!\w)",
    r"(?<!\w)student\s+(?:founder|entrepreneur)(?!\w)",
    r"(?<!\w)student.*(?<!\w)crore-a-month(?!\w)",
)


class RSSService:
    """Fetch, classify, deduplicate, and sort supported news stories."""

    def __init__(
        self,
        feeds: Optional[List[str]] = None,
        freshness_hours: int = 24,
    ):
        self.feeds = feeds or RSS_FEEDS.copy()
        self.freshness_hours = freshness_hours

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()

    @classmethod
    def _entry_text(cls, entry: Any) -> str:
        title = cls._normalize(entry.get("title", ""))
        summary = cls._normalize(
            entry.get("summary", "") or entry.get("description", "")
        )
        source = entry.get("source", {})
        source_title = (
            cls._normalize(source.get("title", ""))
            if hasattr(source, "get")
            else ""
        )

        # Publisher names such as "India Education Diary" must not make an
        # unrelated article appear relevant.
        if source_title:
            title = re.sub(
                rf"\s*-\s*{re.escape(source_title)}\s*$",
                "",
                title,
                flags=re.IGNORECASE,
            )
            summary = re.sub(
                re.escape(source_title),
                " ",
                summary,
                flags=re.IGNORECASE,
            )
        return f" {title} {summary} ".lower()

    @staticmethod
    def _contains_term(text: str, terms: Tuple[str, ...]) -> bool:
        return any(
            re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)
            for term in terms
        )

    @classmethod
    def _category(cls, entry: Any) -> Optional[str]:
        """Return the story category, or ``None`` when it is out of scope."""
        text = cls._entry_text(entry)
        has_ai = cls._contains_term(text, AI_TERMS)
        has_education = cls._contains_term(text, EDUCATION_TERMS)
        has_india = cls._contains_term(text, INDIA_TERMS)
        has_hardware = cls._contains_term(text, HARDWARE_TERMS)

        if any(re.search(pattern, text) for pattern in NON_EDUCATION_PROFILE_PATTERNS):
            has_education = False

        if has_hardware:
            return None

        # AI education is more specific than general AI, so classify it first.
        if has_ai and has_education:
            return "ai_education"

        if has_ai:
            return "ai"

        # Indian education does not require an AI reference.
        if has_india and has_education:
            return "india_education"

        return None

    @staticmethod
    def _published_at(entry: Any) -> Optional[datetime]:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed:
            return None
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        feed_url: str,
    ) -> Any:
        """Download and parse one RSS feed, retrying transient server errors."""
        for attempt in range(1, HTTP_RETRY_ATTEMPTS + 1):
            response = await client.get(feed_url)
            if response.status_code != httpx.codes.SERVICE_UNAVAILABLE:
                response.raise_for_status()
                return feedparser.parse(response.content)

            if attempt == HTTP_RETRY_ATTEMPTS:
                response.raise_for_status()

            delay = 0.5 * (2 ** (attempt - 1))
            logger.warning(
                "Google News returned 503 for %s; retrying in %.1fs "
                "(attempt %d/%d)",
                feed_url,
                delay,
                attempt,
                HTTP_RETRY_ATTEMPTS,
            )
            await asyncio.sleep(delay)

        raise RuntimeError("RSS feed retry loop ended unexpectedly")

    async def get_news(
        self,
        limit: int = 10,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, str]]:
        """Return recent stories from the three supported categories."""
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        cutoff = now - timedelta(hours=self.freshness_hours)

        all_items: List[Dict[str, Any]] = []
        seen_titles = set()
        rejection_counts: Counter = Counter()
        fetch_size = max(limit * 5, 50)

        async with httpx.AsyncClient(
            headers=HTTP_HEADERS,
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            feed_results = await asyncio.gather(
                *(self._fetch_feed(client, feed_url) for feed_url in self.feeds),
                return_exceptions=True,
            )

        for feed_url, feed_result in zip(self.feeds, feed_results):
            if isinstance(feed_result, BaseException):
                rejection_counts["feed_error"] += 1
                logger.error(
                    "Error fetching %s: %s - %s",
                    feed_url,
                    type(feed_result).__name__,
                    feed_result,
                )
                continue

            feed = feed_result
            try:
                for entry in feed.entries[:fetch_size]:
                    title = self._normalize(entry.get("title", ""))
                    link = entry.get("link", "").strip()
                    published_at = self._published_at(entry)
                    normalized_title = title.casefold()
                    category = self._category(entry)

                    if not title or not link:
                        rejection_counts["missing_title_or_link"] += 1
                    elif normalized_title in seen_titles:
                        rejection_counts["duplicate"] += 1
                    elif category is None:
                        rejection_counts["outside_supported_categories"] += 1
                    elif published_at is None:
                        rejection_counts["missing_date"] += 1
                    elif published_at < cutoff:
                        rejection_counts["stale"] += 1
                    elif published_at > now + timedelta(minutes=10):
                        rejection_counts["future_date"] += 1
                    else:
                        source = entry.get("source", {})
                        source_title = (
                            source.get("title", "").strip()
                            if hasattr(source, "get")
                            else ""
                        )
                        all_items.append(
                            {
                                "title": title,
                                "link": link,
                                "published_at": published_at,
                                "source": source_title,
                                "category": category,
                            }
                        )
                        seen_titles.add(normalized_title)
            except Exception as exc:
                rejection_counts["feed_error"] += 1
                logger.error(
                    "Error fetching %s: %s - %s",
                    feed_url,
                    type(exc).__name__,
                    exc,
                )

        all_items.sort(key=lambda item: item["published_at"], reverse=True)
        result = [
            {
                **item,
                "published_at": item["published_at"].isoformat().replace("+00:00", "Z"),
            }
            for item in all_items[:limit]
        ]
        category_counts = Counter(item["category"] for item in result)
        logger.info(
            "RSS result accepted=%d categories=%s rejected=%s",
            len(result),
            dict(category_counts),
            dict(rejection_counts),
        )
        return result

    def add_feed(self, feed_url: str) -> None:
        if feed_url not in self.feeds:
            self.feeds.append(feed_url)

    def remove_feed(self, feed_url: str) -> None:
        if feed_url in self.feeds:
            self.feeds.remove(feed_url)

    async def get_feed_stats(self, sample: int = 5) -> List[Dict[str, Any]]:
        """Return bounded diagnostics for every configured feed."""
        stats: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(
            headers=HTTP_HEADERS,
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            feed_results = await asyncio.gather(
                *(self._fetch_feed(client, feed_url) for feed_url in self.feeds),
                return_exceptions=True,
            )

        for feed_url, feed_result in zip(self.feeds, feed_results):
            if isinstance(feed_result, BaseException):
                logger.error(
                    "Error parsing feed %s: %s", feed_url, feed_result
                )
                stats.append(
                    {
                        "feed": feed_url,
                        "bozo": True,
                        "bozo_exception": (
                            f"{type(feed_result).__name__}: {feed_result}"
                        ),
                        "entries_count": 0,
                        "sample_titles": [],
                    }
                )
                continue

            feed = feed_result
            try:
                entries = getattr(feed, "entries", []) or []
                stats.append(
                    {
                        "feed": feed_url,
                        "bozo": bool(getattr(feed, "bozo", False)),
                        "bozo_exception": (
                            repr(getattr(feed, "bozo_exception", None))
                            if getattr(feed, "bozo_exception", None)
                            else None
                        ),
                        "entries_count": len(entries),
                        "sample_titles": [
                            self._normalize(entry.get("title", ""))
                            for entry in entries[:sample]
                        ],
                    }
                )
            except Exception as exc:
                logger.exception("Error parsing feed %s: %s", feed_url, exc)
                stats.append(
                    {
                        "feed": feed_url,
                        "bozo": True,
                        "bozo_exception": f"{type(exc).__name__}: {exc}",
                        "entries_count": 0,
                        "sample_titles": [],
                    }
                )
        return stats
