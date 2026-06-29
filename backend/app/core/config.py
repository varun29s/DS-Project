"""Application configuration loaded from environment variables / .env file."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # --- App ---
    PROJECT_NAME: str = "Instagram Clone API"
    API_V1_PREFIX: str = "/api/v1"
    # Comma-separated list of allowed CORS origins ("*" allows all)
    BACKEND_CORS_ORIGINS: str = "*"

    # --- Database (Supabase Postgres connection string) ---
    # e.g. postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
    DATABASE_URL: str

    # --- JWT auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- Media storage ---
    # "supabase" (default) or "local" (write to MEDIA_ROOT, served at /media)
    STORAGE_BACKEND: str = "supabase"
    MEDIA_ROOT: str = "media"
    # Public base URL of THIS backend, used to build local media URLs.
    BACKEND_PUBLIC_URL: str = "http://127.0.0.1:8000"

    # --- Supabase Storage (photos / reels) ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # service_role key (server-side only, never expose to clients)
    SUPABASE_STORAGE_BUCKET: str = "media"

    # --- Recommendation (ML) microservice ---
    RECOMMENDER_URL: str = "http://127.0.0.1:8001"
    RECOMMENDER_TIMEOUT: float = 5.0

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # SQLAlchemy requires the "postgresql://" scheme, but some tools emit "postgres://".
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def cors_origins(self) -> list[str]:
        if self.BACKEND_CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()