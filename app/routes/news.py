"""
News routes module for edu-news-ticker.

Defines API endpoints for fetching shortened news headlines.
"""

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query

from app.services.rss_service import RSSService
from app.services.groq_service import GroqService
from app.config import settings


logger = logging.getLogger(__name__)

# Create router for news endpoints
router = APIRouter(prefix="/api/news", tags=["news"])

# Initialize services
rss_service = RSSService()
groq_service = GroqService() if settings.groq_api_key else None


def _truncate_headline(title: str, max_words: int = 10) -> str:
    """Provide a deterministic fallback when Groq is not configured."""
    return " ".join(title.split()[:max_words])


@router.get("", response_model=Dict[str, Any])
async def get_news(
    limit: int = Query(12, ge=1, le=50, description="Number of news items to return")
) -> Dict[str, Any]:
    """
    Fetch and return the latest shortened news headlines.
    
    This endpoint:
    1. Fetches news from multiple RSS feeds
    2. Shortens each headline using Groq API
    3. Returns formatted response with headlines
    
    Query Parameters:
        limit: Number of news items to return (1-50). Defaults to 10.
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - count: Number of news items returned
        - breaking_news: List of shortened headlines
    
    Raises:
        HTTPException: If news fetching or shortening fails.
    
    Example:
        GET /api/news?limit=5
        
        {
            "status": "success",
            "count": 5,
            "breaking_news": [
                "AI tutors improve student learning",
                "Google launches new classroom AI tools",
                "UNESCO releases AI education framework",
                "Microsoft advances AI in education",
                "OpenAI expands education partnerships"
            ]
        }
    """
    try:
        logger.info(f"Fetching {limit} news items")
        
        # Fetch news from RSS feeds
        news_items = rss_service.get_news(limit=limit)
        
        if not news_items:
            logger.warning("No news items fetched from RSS feeds")
            return {
                "status": "success",
                "count": 0,
                "freshness_hours": rss_service.freshness_hours,
                "breaking_news": []
            }
        
        # Extract titles
        titles = [item["title"] for item in news_items]
        
        # Shorten headlines using Groq
        logger.info(f"Shortening {len(titles)} headlines")
        shortened_headlines = (
            groq_service.shorten_headlines_batch(titles, max_words=10)
            if groq_service
            else [_truncate_headline(title, max_words=10) for title in titles]
        )
        
        logger.info(f"Successfully processed {len(shortened_headlines)} headlines")
        
        return {
            "status": "success",
            "count": len(shortened_headlines),
            "freshness_hours": rss_service.freshness_hours,
            "breaking_news": [
                {
                    "headline": headline,
                    "link": item["link"],
                    "published_at": item["published_at"],
                    "source": item["source"],
                }
                for headline, item in zip(shortened_headlines, news_items)
            ],
        }
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching news: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch or process news. Please try again later."
        )


@router.get("/full", response_model=Dict[str, Any])
async def get_full_news(
    limit: int = Query(12, ge=1, le=50, description="Number of news items to return")
) -> Dict[str, Any]:
    """
    Fetch and return full news headlines with links.
    
    This endpoint returns the original full headlines along with their source links,
    useful for providing more detailed information to users.
    
    Query Parameters:
        limit: Number of news items to return (1-50). Defaults to 10.
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - count: Number of news items returned
        - news: List of dicts with "title" and "link"
    
    Example:
        GET /api/news/full?limit=3
        
        {
            "status": "success",
            "count": 3,
            "news": [
                {
                    "title": "Full headline about AI education",
                    "link": "https://..."
                },
                ...
            ]
        }
    """
    try:
        logger.info(f"Fetching {limit} full news items")
        
        # Fetch news from RSS feeds
        news_items = rss_service.get_news(limit=limit)
        
        if not news_items:
            logger.warning("No news items fetched from RSS feeds")
            return {
                "status": "success",
                "count": 0,
                "freshness_hours": rss_service.freshness_hours,
                "news": []
            }
        
        logger.info(f"Successfully fetched {len(news_items)} full news items")
        
        return {
            "status": "success",
            "count": len(news_items),
            "freshness_hours": rss_service.freshness_hours,
            "news": news_items
        }
    
    except Exception as e:
        logger.error(f"Error fetching full news: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch news. Please try again later."
        )


@router.get("/debug", response_model=Dict[str, Any])
async def debug_news() -> Dict[str, Any]:
    """
    Diagnostic endpoint to inspect feed parsing status.

    Returns per-feed parsing results (bozo, entries_count, sample_titles)
    and a quick snapshot of the latest `get_news` output. Intended for
    debugging deployments where feeds may be unreachable or filtered out.
    """
    try:
        stats = rss_service.get_feed_stats(sample=5)
        sample_news = rss_service.get_news(limit=5)
        return {
            "status": "success",
            "feeds": stats,
            "sample_news_count": len(sample_news),
            "sample_news": sample_news,
            "freshness_hours": rss_service.freshness_hours,
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail="Debug failed")


