# app/config.py
from pydantic import BaseSettings, validator
from typing import List

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB settings (for reports only)
    MONGO_URL: str
    MONGO_DB_NAME: str = "scopelabs"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # JWT settings
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Validate MongoDB connection string
    @validator("MONGO_URL")
    def validate_mongo_url(cls, v):
        if not v.startswith("mongodb+srv://") and not v.startswith("mongodb://"):
            raise ValueError("Invalid MongoDB connection string")
        return v
    
    # Validate JWT secret key
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        if len(v) < 3:
            raise ValueError("JWT secret key should be at least 32 characters")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings object
settings = Settings()