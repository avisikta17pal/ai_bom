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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="ai-bom")
    environment: str = Field(default="development")

    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/ai_bom", alias="DATABASE_URL")
    testing: bool = Field(default=False, alias="TESTING")

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    s3: S3Settings = Field(default_factory=S3Settings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    admin_email: str = Field(default="admin@example.com")
    admin_password: str = Field(default="admin123")

    allow_dataset_uploads: bool = Field(default=False)

    prometheus_namespace: str = Field(default="ai_bom")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

