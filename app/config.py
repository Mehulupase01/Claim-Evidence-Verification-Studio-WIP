from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded only from environment variables or a local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    public_base_url: str = "http://localhost:8000"

    storage_backend: Literal["r2"] = "r2"
    r2_endpoint: str | None = None
    r2_access_key_id: SecretStr | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket: str = "claim-verifier"

    verifier_backend: Literal["gemini"] = "gemini"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash-lite"

    max_upload_mb: int = Field(default=10, ge=1, le=50)
    request_timeout_seconds: float = Field(default=20.0, ge=1.0, le=120.0)
    retrieval_top_k: int = Field(default=5, ge=1, le=12)
    chunk_size_chars: int = Field(default=1200, ge=300, le=4000)
    chunk_overlap_chars: int = Field(default=200, ge=0, le=1000)
    max_document_pages: int = Field(default=200, ge=1, le=1000)
    max_extracted_chars: int = Field(default=500_000, ge=10_000, le=5_000_000)

    @model_validator(mode="after")
    def validate_chunk_window(self) -> "Settings":
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError("CHUNK_OVERLAP_CHARS must be smaller than CHUNK_SIZE_CHARS")
        return self

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
