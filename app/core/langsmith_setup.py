"""LangSmith configuration for observability."""
import os
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


def setup_langsmith():
    """Configure LangSmith for tracing and observability."""
    if not settings.LANGSMITH_API_KEY:
        logger.warning("LangSmith API key not set. Tracing will be disabled.")
        return
    
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    
    logger.info(
        "LangSmith configured",
        project=settings.LANGSMITH_PROJECT,
        tracing_enabled=settings.LANGSMITH_TRACING,
    )

