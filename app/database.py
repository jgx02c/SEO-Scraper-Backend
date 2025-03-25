# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Database connection with connection pooling
client = AsyncIOMotorClient(
    settings.MONGO_URL,
    maxPoolSize=10,
    minPoolSize=1,
    maxIdleTimeMS=60000,
    retryWrites=True,
    serverSelectionTimeoutMS=5000
)
db = client[settings.MONGO_DB_NAME]

# Helper functions for database operations
def get_current_time():
    """Get current UTC time for database operations"""
    return datetime.utcnow()

async def init_db():
    """Initialize database with required indexes and settings"""
    try:
        logger.info("Creating database indexes...")
        
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        
        # Analysis collection indexes
        await db.analysis.create_index("user_id", unique=True)
        await db.analysis.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")

# Attach helper functions to db object
db.get_current_time = get_current_time