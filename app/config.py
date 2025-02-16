# app/config.py
from pydantic import BaseSettings, validator
from typing import List

class Settings(BaseSettings):
    MONGO_URL: str
    MONGO_DB_NAME: str = "scopelabs"
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @validator("MONGO_URL")
    def validate_mongo_url(cls, v):
        if not v.startswith("mongodb+srv://") and not v.startswith("mongodb://"):
            raise ValueError("Invalid MongoDB connection string")
        return v
    
    class Config:
        env_file = ".env"

settings = Settings()