try:
    from pydantic import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Moola"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "moola_db"
    
    # 30 days token expiration
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    JWT_SECRET: str = "super-secret-key-moola-bookkeeping-app-2026"
    JWT_ALGORITHM: str = "HS256"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "capacitor://localhost",
        "http://localhost",
        "http://192.168.147.4",
        "http://192.168.147.4:9090",
    ]

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
