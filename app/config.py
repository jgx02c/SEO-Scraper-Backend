# app/config.py
from pydantic import BaseSettings, validator
from typing import List

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB settings
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "scopelabs"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon key
    SUPABASE_SERVICE_KEY: str  # Service role key
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Validate MongoDB connection string
    @validator("MONGODB_URL")
    def validate_mongo_url(cls, v):
        if not v.startswith("mongodb+srv://") and not v.startswith("mongodb://"):
            raise ValueError("Invalid MongoDB connection string")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings object
settings = Settings()