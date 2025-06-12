"""Application configuration."""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Omnex"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")
    LOG_LEVEL: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "postgresql://omnex:omnex@localhost:5432/omnex"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Security
    SECRET_KEY: str = Field(
        default="development-secret-key-change-this-in-production-minimum-32-chars",
        min_length=32
    )
    JWT_SECRET_KEY: str = Field(
        default="jwt-development-secret-key-change-this-in-production-32",
        min_length=32
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Auth Configuration
    ENABLE_MULTI_TENANT: bool = False
    DEFAULT_TENANT_ID: str = "00000000-0000-0000-0000-000000000000"
    DEFAULT_TENANT_NAME: str = "Default"
    DEFAULT_TENANT_SLUG: str = "default"
    
    # Redis Auth Cache
    REDIS_AUTH_CACHE_TTL: int = 300  # 5 minutes
    API_KEY_CACHE_PREFIX: str = "api_key:"
    USER_CACHE_PREFIX: str = "user:"
    TOKEN_BLACKLIST_PREFIX: str = "blacklist:"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # MCP Server
    MCP_SERVER_HOST: str = "0.0.0.0"
    MCP_SERVER_PORT: int = 3000
    MCP_SERVER_WORKERS: int = 4

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()