from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "InterviewOS API"
    app_env: str = "dev"
    app_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["*"]

    email_provider: Literal["console", "smtp", "aws_ses"] = "console"
    email_from: str = "assessment@example.com"
    ses_from_email: str | None = None
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False

    storage_provider: Literal["local", "s3"] = "local"
    local_assets_dir: str = "assets"
    local_assessment_filename: str = "example_assessment.zip"

    assessment_bucket: str = "online-assessments"
    assessment_object_key: str = "assessment.zip"
    presigned_url_expiration_seconds: int = 3600
    reminder_delay_seconds: int = 45 * 60

    aws_region: str = "us-east-1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            if value.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("app_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
