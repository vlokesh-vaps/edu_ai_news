"""
Configuration module for edu-news-ticker.

Loads environment variables from .env file and provides configuration
settings for the application.
"""

import os
from typing import Optional

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    
    This class provides access to all configuration needed by the application.
    """
    
    # Groq API Configuration
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Application Configuration
    app_title: str = "edu-news-ticker"
    app_description: str = "Real-time AI and Education news ticker API"
    app_version: str = "1.0.0"
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        
        Raises:
            ValueError: If any required configuration is missing.
        """
        if not cls.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")


# Global settings instance
settings = Settings()

