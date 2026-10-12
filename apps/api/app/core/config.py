from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Mộc Healthy AI Marketing & Commerce Platform"
    VERSION: str = "0.1.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "info"
    SECRET_KEY: str = "dev_secret_key_moc_healthy"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moc_healthy"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_PROVIDER: str = "minio"
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "moc-healthy-assets"
    STORAGE_USE_SSL: bool = False
    STORAGE_PUBLIC_URL: str = "http://localhost:9000/moc-healthy-assets"

    # AI Engine
    AI_DEFAULT_PROVIDER: str = "mock"

    # Auth & Security
    JWT_SECRET_KEY: str = "dev_jwt_secret_key_moc_healthy_do_not_use_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_RATE_LIMIT_PER_MINUTE: int = 15


settings = Settings()
