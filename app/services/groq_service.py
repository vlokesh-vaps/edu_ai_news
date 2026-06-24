"""
Groq Service module for edu-news-ticker.

Handles text summarization and shortening using the Groq API.
"""

import json
import logging
from typing import Optional

from groq import Groq

from app.config import settings


logger = logging.getLogger(__name__)


class GroqService:
    """
    Service for using the Groq API to shorten news headlines.
    
    Responsibilities:
    - Convert long news titles into concise ticker headlines
    - Use Groq API with llama-3.3-70b-versatile model
    - Ensure headlines are maximum 10 words
    - Return clean text only
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Groq Service.
        
        Args:
            api_key: Groq API key. If not provided, uses settings.groq_api_key.
        
        Raises:
            ValueError: If no API key is provided and settings.groq_api_key is not set.
        """
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = settings.groq_model
    
    def shorten_headline(self, title: str, max_words: int = 10) -> str:
        """
        Convert a long news title into a concise ticker headline.
        
        Uses the Groq API to intelligently shorten news headlines while
        preserving the key information. Ensures the output is concise and
        suitable for display in a news ticker.
        
        Args:
            title: The news title to shorten.
            max_words: Maximum number of words in the output. Defaults to 10.
        
        Returns:
            Shortened headline as clean text.
        
        Raises:
            ValueError: If title is empty.
            Exception: If Groq API call fails.
        
        Example:
            >>> service = GroqService()
            >>> short = service.shorten_headline(
            ...     "A very long news title about AI in education"
            ... )
            >>> print(short)
            "AI transforms educational methods"
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        
        try:
            # Prepare the prompt for Groq
            prompt = (
                f"Shorten this news headline to maximum {max_words} words. "
                f"Make it concise, clear, and suitable for a news ticker. "
                f"Return ONLY the shortened headline, no quotes, no explanation.\n\n"
                f"Original headline: {title.strip()}"
            )
            
            logger.debug(f"Sending headline to Groq for shortening: {title[:50]}...")
            
            # Call Groq API
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent results
                max_tokens=50,    # Keep response short
            )
            
            # Extract and clean the response
            shortened = message.choices[0].message.content.strip()
            
            # Remove any quotes if present
            shortened = shortened.strip('"\'')
            
            logger.info(f"Successfully shortened headline from {len(title.split())} "
                       f"to {len(shortened.split())} words")
            
            return shortened
            
        except Exception as e:
            logger.error(f"Error shortening headline with Groq: {type(e).__name__} - {str(e)}")
            # Fallback: return original title truncated
            words = title.split()
            if len(words) > max_words:
                logger.warning(f"Using fallback - truncating to {max_words} words")
                return " ".join(words[:max_words])
            return title
    
    def shorten_headlines_batch(self, titles: list, max_words: int = 10) -> list:
        """
        Shorten multiple headlines at once.
        
        Args:
            titles: List of news titles to shorten.
            max_words: Maximum number of words in each output. Defaults to 10.
        
        Returns:
            List of shortened headlines.
        """
        if not titles:
            return []

        fallback = [" ".join(title.split()[:max_words]) for title in titles]
        prompt = (
            f"Shorten each headline to at most {max_words} words. Preserve names "
            "and facts. Return only a valid JSON array of strings in the same "
            f"order, containing exactly {len(titles)} items.\n\n"
            f"Headlines:\n{json.dumps(titles, ensure_ascii=False)}"
        )

        try:
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max(100, len(titles) * 20),
            )
            content = message.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.removeprefix("```json").removeprefix("```")
                content = content.removesuffix("```").strip()

            shortened = json.loads(content)
            if (
                not isinstance(shortened, list)
                or len(shortened) != len(titles)
                or not all(isinstance(item, str) and item.strip() for item in shortened)
            ):
                raise ValueError("Groq returned an invalid headline batch")

            return [
                " ".join(item.strip().strip("\"'").split()[:max_words])
                for item in shortened
            ]
        except Exception as e:
            logger.error(
                "Batch headline shortening failed; using local fallback: %s",
                str(e),
            )
            return fallback

