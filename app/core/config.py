"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Healthcare Agentic RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_HEADER_NAME: str = "X-API-Key"
    
    # AI Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # "openai" or "anthropic"
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"  # or your Pinecone environment
    PINECONE_INDEX_NAME: str = "healthcare-knowledge-base"
    
    # LangSmith
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "healthcare-rag"
    LANGSMITH_TRACING: bool = True
    
    # Tavily (Real-time Web Search)
    TAVILY_API_KEY: str = ""
    TAVILY_ENABLED: bool = True
    TAVILY_MAX_RESULTS: int = 5
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

