import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Teacher AI Platform")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "change-in-production")
    JWT_ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    LLM_FALLBACK_CHAIN = os.getenv("LLM_FALLBACK_CHAIN", "")

    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))

    CORS_ORIGINS = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173"]'))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @property
    def api_keys(self) -> list[str]:
        return [k.strip() for k in self.GOOGLE_API_KEY.split(",") if k.strip()]

    @property
    def fallback_models(self) -> list[str]:
        return [m.strip() for m in self.LLM_FALLBACK_CHAIN.split(",") if m.strip()]


settings = Settings()
