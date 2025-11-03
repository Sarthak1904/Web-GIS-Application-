"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Enterprise Geospatial Intelligence Platform"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/v1"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Database
    database_url: str = "postgresql+psycopg2://geospatial:geospatial@localhost:5432/geospatial_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # GeoServer
    geoserver_url: str = "http://localhost:8080/geoserver"
    geoserver_user: str = "admin"
    geoserver_password: str = "geoserver"

    # Ingestion
    max_upload_size_mb: int = 500
    default_crs: str = "EPSG:4326"
    allowed_crs: str = "EPSG:4326,EPSG:3857,EPSG:32618,EPSG:2278"

    # Pagination
    default_page_size: int = 100
    max_page_size: int = 1000

    @property
    def allowed_crs_list(self) -> List[str]:
        """Parse allowed CRS string into list."""
        return [c.strip() for c in self.allowed_crs.split(",") if c.strip()]

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            return "INFO"
        return v.upper()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
