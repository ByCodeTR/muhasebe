"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # App
    app_name: str = "Muhasebe API"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/muhasebe"
    
    @property
    def async_database_url(self) -> str:
        """Convert standard postgresql:// URL to asyncpg format."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    
    # OCR
    tesseract_path: Optional[str] = None
    
    # File Storage
    upload_dir: str = "uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # Optional: Cloudinary
    cloudinary_url: Optional[str] = None
    
    # Optional: Google Vision OCR fallback
    google_vision_api_key: Optional[str] = None
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
