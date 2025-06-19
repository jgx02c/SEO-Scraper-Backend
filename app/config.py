# app/config.py
from pydantic import BaseSettings, validator
from typing import List, Union
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGODB_DB_NAME: str = os.getenv("MONGO_DB_NAME")
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")
    
    POSTGRES_URI = os.getenv("POSTGRES_URI")
    
    # CORS settings (defined as Union to prevent automatic JSON parsing)
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]
    
    # Validate MongoDB connection string
    @validator("MONGODB_URL")
    def validate_mongo_url(cls, v):
        if not v.startswith("mongodb+srv://") and not v.startswith("mongodb://"):
            raise ValueError("Invalid MongoDB connection string")
        return v
    
    # Validate PostgreSQL connection string
    @validator("POSTGRES_URI")
    def validate_postgres_uri(cls, v):
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError("Invalid PostgreSQL connection string. Must start with postgresql:// or postgres://")
        return v
    
    # Handle CORS_ORIGINS parsing from environment - convert to List[str]
    @validator("CORS_ORIGINS", pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle the malformed JSON in .env file
            if v.startswith('["') and v.endswith('"]'):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # If JSON parsing fails, treat as comma-separated string
            return [origin.strip().strip('"[]') for origin in v.split(',')]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]  # Default fallback
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings object
settings = Settings()