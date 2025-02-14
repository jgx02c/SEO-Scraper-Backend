from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://PiclistAccess:4v2XQfs9xLKaP9nf@piclistdatabase.4tprg.mongodb.net/?retryWrites=true&w=majority&appName=PiclistDatabase")
DATABASE_NAME = "PiclistDatabase"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

def get_collection(collection_name: str):
    return db[collection_name]
