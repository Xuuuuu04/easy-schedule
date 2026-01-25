from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 3306
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_CHARSET: str = "utf8mb4"
    DB_AUTOCOMMIT: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # AI / LLM
    SILICON_FLOW_API_KEY: Optional[str] = None
    SILICON_FLOW_BASE_URL: Optional[AnyHttpUrl] = None
    SILICON_FLOW_MODEL_NAME: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
