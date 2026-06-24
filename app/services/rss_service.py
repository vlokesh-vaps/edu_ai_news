"""Fetch fresh, strictly education-related news from RSS feeds."""

import calendar
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.error import URLError
import os

import feedparser


logger = logging.getLogger(__name__)


# Queries are restricted to the last day at the source. The service also checks
# every publication timestamp locally, so stale or undated stories cannot leak in.
RSS_FEEDS: List[str] = [
    (
        "https://news.google.com/rss/search?"
        "q=India+(education+OR+schools+OR+universities)+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
    (
        "https://news.google.com/rss/search?"
        "q=India+(%22AI+in+education%22+OR+%22education+AI%22+OR+EdTech)+when:1d"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
]

EDUCATION_TERMS = (
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
    "higher ed",
    "higher education",
    "k-12",
    "k12",
    "academic",
    "academics",
    "scholarship",
    "scholarships",
)

AMBIGUOUS_EDUCATION_TERMS = ("school", "schools", "learning")
NON_EDUCATION_PROFILE_PATTERNS = (
    r"(?<!\w)built\s+(?:an?\s+)?(?:rs\.?\s*)?[\w\s-]*business(?!\w)",
    r"(?<!\w)student\s+(?:founder|entrepreneur)(?!\w)",
    r"(?<!\w)student.*(?<!\w)crore-a-month(?!\w)",
)

INDIA_TERMS = (
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
    "dombivali",
    "dombivli",
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


class RSSService:
    """Fetch, validate, deduplicate, and sort current education news."""

    def __init__(
        self,
        feeds: Optional[List[str]] = None,
        freshness_hours: int = 24,
    ):
        """
        Initialize RSSService.

        Args:
            feeds: optional list of feed URLs. Defaults to internal RSS_FEEDS.
            freshness_hours: how far back (hours) to accept published items.

        The service can be configured to restrict to India-only stories via the
        environment variable `ONLY_INDIA`. By default `ONLY_INDIA` is `true`.
        Set `ONLY_INDIA=false` in production to allow global news (useful for
        debugging or broader coverage).
        """
        self.feeds = feeds or RSS_FEEDS
        self.freshness_hours = freshness_hours
        only_india = os.getenv("ONLY_INDIA", "true").strip().lower()
        self.only_india = only_india not in ("0", "false", "no", "off")

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()

    @classmethod
    def _is_education_news(cls, entry: Any) -> bool:
        text = cls._entry_text(entry)
        if any(re.search(pattern, text) for pattern in NON_EDUCATION_PROFILE_PATTERNS):
            return False
        strong_terms = tuple(
            term for term in EDUCATION_TERMS if term not in AMBIGUOUS_EDUCATION_TERMS
        )
        if cls._contains_term(text, strong_terms):
            return True

        # These words can be verbs or appear outside education. Require nearby
        # education context instead of accepting them by themselves.
        return bool(
            re.search(
                r"(?<!\w)(school|schools|learning)(?!\w).{0,50}"
                r"(?<!\w)(student|teacher|classroom|education|curriculum|exam|learning)(?!\w)"
                r"|(?<!\w)(student|teacher|classroom|education|curriculum|exam|learning)(?!\w)"
                r".{0,50}(?<!\w)(school|schools|learning|Job|AI|Carrer)(?!\w)",
                text,
            )
        )

    @classmethod
    def _is_india_news(cls, entry: Any) -> bool:
        return cls._contains_term(cls._entry_text(entry), INDIA_TERMS)

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
    def _contains_term(text: str, terms: tuple) -> bool:
        return any(
            re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text)
            for term in terms
        )

    @staticmethod
    def _published_at(entry: Any) -> Optional[datetime]:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed:
            return None
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)

    def get_news(
        self,
        limit: int = 10,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, str]]:
        """Return only education stories published during the freshness window."""
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        cutoff = now - timedelta(hours=self.freshness_hours)

        all_items: List[Dict[str, Any]] = []
        seen_titles = set()
        fetch_size = max(limit * 5, 50)

        for feed_url in self.feeds:
            try:
                logger.info("Fetching education RSS feed: %s", feed_url)
                # Allow an optional custom User-Agent to avoid blocking by some
                # feed providers. Set the env var FEED_USER_AGENT if needed.
                user_agent = os.getenv("FEED_USER_AGENT", None)
                if user_agent:
                    feed = feedparser.parse(feed_url, request_headers={"User-Agent": user_agent})
                else:
                    feed = feedparser.parse(feed_url)
                if feed.bozo and isinstance(feed.bozo_exception, URLError):
                    logger.warning("Failed to fetch %s: %s", feed_url, feed.bozo_exception)
                    continue

                for entry in feed.entries[:fetch_size]:
                    title = self._normalize(entry.get("title", ""))
                    published_at = self._published_at(entry)
                    normalized_title = title.casefold()

                    if (
                        not title
                        or not entry.get("link", "").strip()
                        or normalized_title in seen_titles
                        or not self._is_education_news(entry)
                        or (self.only_india and not self._is_india_news(entry))
                        or published_at is None
                        or published_at < cutoff
                        or published_at > now + timedelta(minutes=10)
                    ):
                        continue

                    source = entry.get("source", {})
                    source_title = (
                        source.get("title", "").strip()
                        if hasattr(source, "get")
                        else ""
                    )
                    all_items.append(
                        {
                            "title": title,
                            "link": entry.get("link", "").strip(),
                            "published_at": published_at,
                            "source": source_title,
                        }
                    )
                    seen_titles.add(normalized_title)
            except Exception as exc:
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
        logger.info("Returning %d fresh India education news items", len(result))
        return result

    def add_feed(self, feed_url: str) -> None:
        if feed_url not in self.feeds:
            self.feeds.append(feed_url)

    def remove_feed(self, feed_url: str) -> None:
        if feed_url in self.feeds:
            self.feeds.remove(feed_url)

    def get_feed_stats(self, sample: int = 5) -> List[Dict[str, Any]]:
        """
        Return diagnostic information about each configured feed.

        Useful for debugging deploys where feeds may be unreachable or
        returning unexpected content. For each feed this returns whether
        feedparser reported a `bozo` (parse) error, the number of entries
        discovered, and a small sample of titles.

        Args:
            sample: number of sample titles to include per feed.

        Returns:
            List of dicts with keys: feed, bozo, bozo_exception, entries_count, sample_titles
        """
        stats: List[Dict[str, Any]] = []
        for feed_url in self.feeds:
            try:
                logger.info("Parsing feed for diagnostics: %s", feed_url)
                user_agent = os.getenv("FEED_USER_AGENT", None)
                if user_agent:
                    feed = feedparser.parse(feed_url, request_headers={"User-Agent": user_agent})
                else:
                    feed = feedparser.parse(feed_url)
                bozo = bool(getattr(feed, "bozo", False))
                bozo_exc = getattr(feed, "bozo_exception", None)
                entries = getattr(feed, "entries", []) or []
                sample_titles = []
                for entry in entries[:sample]:
                    title = self._normalize(entry.get("title", ""))
                    sample_titles.append(title)
                stats.append(
                    {
                        "feed": feed_url,
                        "bozo": bozo,
                        "bozo_exception": repr(bozo_exc) if bozo_exc else None,
                        "entries_count": len(entries),
                        "sample_titles": sample_titles,
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
