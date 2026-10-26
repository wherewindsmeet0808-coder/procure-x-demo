import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "PROCURE-X"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./procurement.db")
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
