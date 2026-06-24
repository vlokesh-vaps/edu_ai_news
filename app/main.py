"""
Main application module for edu-news-ticker.

Creates and configures the FastAPI application with all middleware,
routes, and error handling.
"""

import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.routes import news


# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Do not fail module import in a serverless cold start. The full-news endpoint
# works without Groq, while the shortened endpoint has a local fallback.
if settings.groq_api_key:
    logger.info("Groq configuration detected")
else:
    logger.warning(
        "GROQ_API_KEY is not set; shortened headlines will use local truncation"
    )


# Lifespan handler to replace deprecated on_event startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager called on application startup and shutdown.
    Replaces the deprecated @app.on_event("startup") / @app.on_event("shutdown").
    """
    logger.info(f"Starting {settings.app_title} v{settings.app_version}")
    logger.info("Application ready to accept requests")
    try:
        yield
    finally:
        logger.info(f"Shutting down {settings.app_title}")

# Create FastAPI application with lifespan handler
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)


# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(news.router)


# Health check endpoint
@app.get("/", tags=["health"])
async def health_check() -> dict:
    """
    Health check endpoint for monitoring application status.
    
    Returns:
        {"status": "running"} if the application is healthy.
    
    Example:
        GET /
        
        {
            "status": "running"
        }
    """
    logger.debug("Health check requested")
    return {"status": "running"}


# Root endpoint
@app.get("/api", tags=["health"])
async def api_health() -> dict:
    """
    API health check endpoint.
    
    Returns:
        Information about the API.
    
    Example:
        GET /api
        
        {
            "status": "running",
            "service": "edu-news-ticker",
            "version": "1.0.0"
        }
    """
    logger.debug("API health check requested")
    return {
        "status": "running",
        "service": settings.app_title,
        "version": settings.app_version
    }


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handle unhandled exceptions globally.
    
    Args:
        request: The request object
        exc: The exception
    
    Returns:
        JSON response with error details
    """
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Internal server error. Please try again later."
        }
    )


# (startup/shutdown logging is handled by the lifespan context manager above)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app",host="0.0.0.0",port=8000,reload=True,
        log_level=settings.log_level.lower()
    )

