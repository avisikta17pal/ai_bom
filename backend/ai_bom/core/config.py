from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    secret_key: str = Field(default="changeme")
    access_token_expires_minutes: int = Field(default=60 * 24)
    algorithm: str = Field(default="HS256")


class S3Settings(BaseModel):
    endpoint: str = Field(default="minio:9000")
    access_key: str = Field(default="minioadmin")
    secret_key: str = Field(default="minioadmin")
    bucket: str = Field(default="ai-bom")
    secure: bool = Field(default=False)
    kms_key_id: str | None = Field(default=None)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ai-bom")
    environment: str = Field(default="development")

    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/ai_bom", alias="DATABASE_URL")
    testing: bool = Field(default=False, alias="TESTING")

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    s3: S3Settings = Field(default_factory=S3Settings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])  # tighten in prod

    admin_email: str = Field(default="admin@example.com")
    admin_password: str = Field(default="admin123")

    allow_dataset_uploads: bool = Field(default=False)
    require_https: bool = Field(default=False)
    hsts_max_age: int = Field(default=31536000)
    csp_policy: str = Field(default="default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'")
    max_upload_mb: int = Field(default=512)
    allowed_upload_mime_types: list[str] = Field(default_factory=lambda: ["application/octet-stream", "application/x-hdf5", "application/zip", "text/csv"])

    prometheus_namespace: str = Field(default="ai_bom")
    otlp_endpoint: str | None = Field(default=None)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

