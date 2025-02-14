import redis
import json
import os
from dotenv import load_dotenv 
from fastapi import HTTPException

load_dotenv()

# Redis connection setup (no CacheConfig, no protocol)
cache = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True  # Ensures data is returned as strings
)

async def get_key(toGet: str):  
    """Retrieve a value from Redis based on a key."""
    try:
        toRet = cache.get(toGet)  # No `await`, since redis-py is synchronous
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis get error: {str(e)}")
    
    return toRet

# Existing Redis function to add API keys
async def add_key(api_key_data):  
    """Add an API key to Redis."""
    good = False
    try:  
        cache.set(f"api_key:{api_key_data['apiKey']}", json.dumps(api_key_data))  # No `await`
        good = True
    except Exception as e:  
        raise HTTPException(status_code=500, detail=f"Redis set error: {str(e)}")

    return good
