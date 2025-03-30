# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Database connection with connection pooling (for reports only)
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
    """Initialize database with required indexes for reports"""
    try:
        logger.info("Creating database indexes for reports...")
        
        # Reports collection indexes
        await db.reports.create_index("business_id")
        await db.reports.create_index([("business_id", 1), ("report_date", -1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")

# Attach helper functions to db object
db.get_current_time = get_current_time