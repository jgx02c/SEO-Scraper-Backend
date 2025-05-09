from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
import logging
from .db.supabase import supabase, admin_supabase

logger = logging.getLogger(__name__)

# Initialize MongoDB client
mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
db = mongo_client[settings.MONGODB_DB_NAME]

async def init_db():
    """Initialize database connections"""
    try:
        # Test MongoDB connection
        await db.command('ping')
        logger.info("MongoDB connection established")
        
        # Supabase connection is tested when auth is needed
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise 