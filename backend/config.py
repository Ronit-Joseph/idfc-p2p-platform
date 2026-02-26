from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./p2p.db"
    DATABASE_URL_SYNC: str = "sqlite:///./p2p.db"
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000"]
    ENABLE_DOCS: bool = True
    AUTH_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
