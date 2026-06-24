import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.services.rss_service import RSSService


class RSSServiceCategoryTests(unittest.TestCase):
    NOW = datetime(2026, 6, 24, 12, 0, tzinfo=timezone.utc)

    @patch("app.services.rss_service.feedparser.parse")
    def test_returns_all_three_supported_categories(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("OpenAI launches a new AI coding assistant", 11),
            self._entry("Teachers use AI to personalize classroom learning", 10),
            self._entry("CBSE updates student assessment rules in India", 9),
            self._entry("India launches a new tourism campaign", 8),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(
            [(item["title"], item["category"]) for item in result],
            [
                ("OpenAI launches a new AI coding assistant", "ai"),
                (
                    "Teachers use AI to personalize classroom learning",
                    "ai_education",
                ),
                (
                    "CBSE updates student assessment rules in India",
                    "india_education",
                ),
            ],
        )

    @patch("app.services.rss_service.feedparser.parse")
    def test_rejects_hardware_news(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("Nvidia launches new AI GPU for data centers", 11),
            self._entry("India opens a semiconductor manufacturing plant", 10),
            self._entry("New smartphone adds generative AI processor", 9),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(result, [])

    @patch("app.services.rss_service.feedparser.parse")
    def test_rejects_hardware_even_with_education_context(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("Schools use AI robots to help students learn", 11),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(result, [])

    @patch("app.services.rss_service.feedparser.parse")
    def test_indian_reference_is_not_required_for_general_ai_news(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("Anthropic releases an AI safety research report", 11),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(result[0]["category"], "ai")

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

    @patch("app.services.rss_service.feedparser.parse")
    def test_rejects_stale_and_undated_news(self, parse):
        parse.return_value.bozo = False
        parse.return_value.entries = [
            self._entry("OpenAI publishes new AI research", 11, day=22),
            self._entry("AI changes software development", None),
        ]

        result = RSSService(feeds=["test"]).get_news(limit=10, now=self.NOW)

        self.assertEqual(result, [])

    @staticmethod
    def _entry(hour_title, hour, day=24, source="Test News"):
        entry = {
            "title": hour_title,
            "link": f"https://example.com/{hour}-{day}",
            "summary": hour_title,
            "source": {"title": source},
        }
        if hour is not None:
            entry["published_parsed"] = (2026, 6, day, hour, 0, 0, 0, 0, 0)
        return entry


if __name__ == "__main__":
    unittest.main()
