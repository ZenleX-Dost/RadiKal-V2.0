"""
Production configuration management.

Environment variables for different deployment stages:
- Development
- Staging
- Production
"""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Pydantic v2 configuration - allow extra fields from .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars without error
    )
    
    # Application
    APP_NAME: str = "RadiKal XAI Quality Control"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    
    # Security - Now with defaults for development
    SECRET_KEY: str = Field(default="")  # Will be validated
    JWT_SECRET: str = Field(default="")  # Backwards compat
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"]
    )
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3001")  # Backwards compat
    
    # Database
    DATABASE_TYPE: str = Field(default="supabase")
    SUPABASE_DB_URL: str = Field(default="")  # Will read from env
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    
    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")
    
    # ML Models
    DEVICE: str = Field(default="cuda")
    YOLO_MODEL_PATH: str = Field(
        default="models/yolo/classification_defect_focused/weights/best.pt"
    )
    BATCH_SIZE: int = Field(default=16)
    CONFIDENCE_THRESHOLD: float = Field(default=0.5)
    
    # MLflow
    MLFLOW_TRACKING_URI: Optional[str] = Field(default=None)
    MLFLOW_EXPERIMENT_NAME: str = Field(default="radikal-xai")
    
    # Storage
    UPLOAD_DIR: str = Field(default="data/uploads")
    EXPORTS_DIR: str = Field(default="exports")
    MAX_UPLOAD_SIZE_MB: int = Field(default=10)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default="logs/app.log")
    
    # Email (for alerts)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    ALERT_EMAIL: Optional[str] = Field(default=None)
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    def get_secret_key(self) -> str:
        """Get the secret key, preferring SECRET_KEY over JWT_SECRET."""
        key = self.SECRET_KEY or self.JWT_SECRET
        if not key and self.ENVIRONMENT == "production":
            raise ValueError("SECRET_KEY is required in production")
        return key or "dev-only-insecure-key"


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Export for easy import
settings = get_settings()
