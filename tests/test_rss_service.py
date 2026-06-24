import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.services.rss_service import RSSService


class RSSServiceIndiaTests(unittest.TestCase):
    NOW = datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)

    @patch("app.services.rss_service.feedparser.parse")
    def test_returns_only_fresh_india_education_news(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("Delhi schools introduce AI learning tools", 11),
            self._entry("US schools introduce AI learning tools", 10),
            self._entry("India launches a new semiconductor program", 9),
            self._entry("CBSE updates student assessment rules", 8),
            self._entry(
                "India schools Islamabad over remarks at the UN",
                7,
            ),
            self._entry(
                "Indian student built a Rs 1 crore-a-month AI business",
                6,
            ),
            self._entry("Indian university announces old policy", 5, day=22),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(
            [item["title"] for item in result],
            [
                "Delhi schools introduce AI learning tools",
                "CBSE updates student assessment rules",
            ],
        )

    @patch("app.services.rss_service.feedparser.parse")
    def test_localized_feed_does_not_make_foreign_story_indian(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("London university changes admissions policy", 11),
        ]

        result = RSSService(feeds=["india-localized-feed"]).get_news(
            limit=10, now=self.NOW
        )

        self.assertEqual(result, [])

    @patch("app.services.rss_service.feedparser.parse")
    def test_publisher_name_cannot_supply_relevance(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry(
                "Company appoints new technology executive - India Education Diary",
                11,
                source="India Education Diary",
            ),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(result, [])

    @staticmethod
    def _entry(title, hour, day=24, source="Test News"):
        return {
            "title": title,
            "link": f"https://example.com/{hour}-{day}",
            "summary": title,
            "published_parsed": (2026, 6, day, hour, 0, 0, 0, 0, 0),
            "source": {"title": source},
        }


if __name__ == "__main__":
    unittest.main()
