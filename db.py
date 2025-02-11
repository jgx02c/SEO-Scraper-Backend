import os
from pymongo import MongoClient
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def init_mongodb():
    """Initialize MongoDB connection"""
    try:
        client = MongoClient(
            os.getenv('MONGODB_URI'),
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        # Test the connection
        client.server_info()
        db = client.get_database(os.getenv('MONGODB_DB_NAME'))
        logger.info("Successfully connected to MongoDB")
        return client, db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

# Initialize MongoDB and collections
try:
    mongo_client, db = init_mongodb()
    business_collection = db.business
    webpages_collection = db.webpages
    chat_collection = db.chats
    settings_collection = db.settings   
except Exception as e:
    logger.error(f"Failed to initialize MongoDB collections: {e}")
    raise
