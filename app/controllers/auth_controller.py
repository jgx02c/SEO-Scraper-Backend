# app/controllers/auth_controller.py
from fastapi import HTTPException, status
from ..models.user import UserCreate, UserLogin, UserInDB, Token
from ..utils.security import verify_password, get_password_hash, create_access_token
from ..dependencies import db

class AuthController:
    @staticmethod
    async def signup(user: UserCreate) -> Token:
        # Check if user exists
        if await db.users.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_data = UserInDB(
            email=user.email,
            hashed_password=get_password_hash(user.password)
        )
        
        await db.users.insert_one(user_data.dict())
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    async def signin(user: UserLogin) -> Token:
        db_user = await db.users.find_one({"email": user.email})
        if not db_user or not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        access_token = create_access_token(data={"sub": user.email})
        return Token(access_token=access_token, token_type="bearer")