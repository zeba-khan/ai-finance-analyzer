from pydantic_settings import BaseSettings  # type: ignore[import]
from functools import lru_cache
import os


class Settings(BaseSettings):
    database_url: str = "sqlite:///./finance.db"
    groq_api_key: str = ""
    secret_key: str = "dev-secret-key"
    environment: str = "development"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
