# app/config.py
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    MONGO_URL: str = "mongodb://localhost:27017"
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()