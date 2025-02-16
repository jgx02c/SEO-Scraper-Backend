# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from jose import JWTError, jwt
import asyncio

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/signin")

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

# Create indexes for the users collection
async def init_db():
    try:
        await db.users.create_index("email", unique=True)
    except Exception as e:
        print(f"Error creating index: {e}")

# Initialize DB on startup
asyncio.create_task(init_db())

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user