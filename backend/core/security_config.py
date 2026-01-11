"""
Secure configuration management for RadiKal backend.

This module provides:
- Environment-based configuration
- Secure secret handling
- Configuration validation
- Default secure values
"""

import os
import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)


def generate_secret_key() -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(64)


class SecuritySettings(BaseSettings):
    """Security-focused settings with validation."""
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default_factory=generate_secret_key,
        description="JWT signing secret - MUST be set in production"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    
    # API Security
    API_KEY_HEADER: str = Field(default="X-API-Key")
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=10, le=10000)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, ge=10, le=3600)
    
    # CORS Configuration  
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH"])
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token"]
    )
    
    # File Upload Security
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
    )
    ALLOWED_CONTENT_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/bmp", "image/tiff"]
    )
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = Field(default=True)
    CONTENT_SECURITY_POLICY: str = Field(
        default="default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'"
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret is secure enough."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        
        # Check for known insecure defaults
        insecure_defaults = [
            "dev-secret-key-change-in-production",
            "radikal-dev-secret-change-in-production",
            "secret",
            "changeme",
            "your-secret-key",
        ]
        if v.lower() in [s.lower() for s in insecure_defaults]:
            logger.warning(
                "SECURITY WARNING: Using insecure default JWT secret! "
                "Set JWT_SECRET_KEY environment variable for production."
            )
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError(
                    "Cannot use default JWT secret in production. "
                    "Set JWT_SECRET_KEY environment variable."
                )
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {valid_envs}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    
    DATABASE_TYPE: str = Field(default="sqlite")
    DATABASE_URL: Optional[str] = Field(default=None)
    
    # Supabase settings (if used)
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None)
    SUPABASE_DB_URL: Optional[str] = Field(default=None)
    
    # Connection pool settings
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_PRE_PING: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class Settings(SecuritySettings, DatabaseSettings):
    """Combined application settings."""
    
    # Application
    APP_NAME: str = Field(default="RadiKal XAI Quality Control")
    APP_VERSION: str = Field(default="2.0.0")
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000, ge=1, le=65535)
    WORKERS: int = Field(default=1, ge=1, le=32)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default=None)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.DEBUG and not self.is_production


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        
        # Log security warnings
        if _settings.is_production:
            if _settings.DEBUG:
                logger.warning("DEBUG mode should be disabled in production!")
            if not _settings.ENABLE_SECURITY_HEADERS:
                logger.warning("Security headers are disabled in production!")
    
    return _settings


def reset_settings() -> None:
    """Reset settings (for testing)."""
    global _settings
    _settings = None


# Export settings instance
settings = get_settings()
