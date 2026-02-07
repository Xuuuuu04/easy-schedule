import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

class Settings(BaseModel):
    # API Keys
    SILICON_FLOW_API_KEY: str = os.getenv("SILICON_FLOW_API_KEY", "")
    SILICON_FLOW_BASE_URL: str = os.getenv("SILICON_FLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    SILICON_FLOW_MODEL_NAME: str = os.getenv("SILICON_FLOW_MODEL_NAME", "zai-org/GLM-4.6")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "course_scheduling")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))

settings = Settings()
