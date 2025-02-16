# app/controllers/auth_controller.py
from fastapi import HTTPException, status
from ..models.user import UserCreate, UserLogin, UserInDB, Token, PasswordResetRequest, PasswordReset
from ..utils.security import verify_password, get_password_hash, create_access_token
from ..dependencies import db
from datetime import datetime, timedelta
import secrets

class AuthController:
    @staticmethod
    async def signup(user: UserCreate) -> dict:
        # Check if user exists
        if await db.users.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_data = UserInDB(
            email=user.email,
            hashed_password=get_password_hash(user.password),
            created_at=datetime.utcnow()
        )
        
        await db.users.insert_one(user_data.dict())
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        # Return both token and user data
        return {
            "success": True,
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "hasCompletedOnboarding": False
            }
        }

    @staticmethod
    async def signin(user: UserLogin) -> dict:
        db_user = await db.users.find_one({"email": user.email})
        if not db_user or not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        # Return both token and user data
        return {
            "success": True,
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "hasCompletedOnboarding": db_user.get("has_completed_onboarding", False)
            }
        }

    @staticmethod
    async def forgot_password(request: PasswordResetRequest) -> dict:
        user = await db.users.find_one({"email": request.email})
        if not user:
            # Return success even if user doesn't exist for security
            return {
                "success": True,
                "message": "If an account exists with this email, you will receive a password reset link"
            }
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token in database
        await db.users.update_one(
            {"email": request.email},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_token_expires
                }
            }
        )
        
        # Here you would typically send an email with the reset link
        # For now, we'll just return the token (in production, send via email)
        return {
            "success": True,
            "message": "Password reset instructions sent",
            "debug_token": reset_token  # Remove in production
        }

    @staticmethod
    async def reset_password(reset_data: PasswordReset) -> dict:
        # Find user with valid reset token
        user = await db.users.find_one({
            "reset_token": reset_data.token,
            "reset_token_expires": {"$gt": datetime.utcnow()}
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password and clear reset token
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "hashed_password": get_password_hash(reset_data.new_password)
                },
                "$unset": {
                    "reset_token": "",
                    "reset_token_expires": ""
                }
            }
        )
        
        return {
            "success": True,
            "message": "Password has been reset successfully"
        }