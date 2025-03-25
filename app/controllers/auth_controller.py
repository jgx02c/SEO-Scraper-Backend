# app/controllers/auth_controller.py
from fastapi import HTTPException, status
from ..models.user import UserCreate, UserLogin, UserInDB, Token, PasswordResetRequest, PasswordReset
from ..utils.jwt_handler import create_access_token
from ..utils.security import verify_password, get_password_hash
from ..database import db
from datetime import datetime, timedelta
import secrets
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AuthController:
    @staticmethod
    async def signup(user: UserCreate) -> dict:
        """
        Register a new user
        
        Args:
            user (UserCreate): User registration data
            
        Returns:
            dict: Response with token and user data
            
        Raises:
            HTTPException: If email already exists
        """
        try:
            # Check if user exists
            if await db.users.find_one({"email": user.email}):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user
            user_id = str(ObjectId())
            user_data = UserInDB(
                id=user_id,
                email=user.email,
                hashed_password=get_password_hash(user.password),
                created_at=datetime.utcnow(),
                roles=["user"]
            )
            
            await db.users.insert_one(user_data.dict())
            
            # Create access token with user ID and roles
            token_data = {
                "sub": user.email,
                "user_id": user_id,
                "roles": ["user"]
            }
            access_token = create_access_token(data=token_data)
            
            # Return both token and user data
            return {
                "success": True,
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": user.email,
                    "hasCompletedOnboarding": False,
                    "roles": ["user"]
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in signup: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user account"
            )

    @staticmethod
    async def signin(user: UserLogin) -> dict:
        """
        Authenticate a user and return a JWT token
        
        Args:
            user (UserLogin): User login credentials
            
        Returns:
            dict: Response with token and user data
            
        Raises:
            HTTPException: If credentials are invalid
        """
        try:
            db_user = await db.users.find_one({"email": user.email})
            if not db_user or not verify_password(user.password, db_user["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Create access token with user ID and roles
            token_data = {
                "sub": user.email,
                "user_id": str(db_user["_id"]),
                "roles": db_user.get("roles", ["user"])
            }
            access_token = create_access_token(data=token_data)
            
            # Return both token and user data
            return {
                "success": True,
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(db_user["_id"]),
                    "email": user.email,
                    "hasCompletedOnboarding": db_user.get("has_completed_onboarding", False),
                    "roles": db_user.get("roles", ["user"])
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in signin: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )

    @staticmethod
    async def forgot_password(request: PasswordResetRequest) -> dict:
        """
        Initiate password reset process
        
        Args:
            request (PasswordResetRequest): Password reset request with email
            
        Returns:
            dict: Response with success status
        """
        try:
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
        except Exception as e:
            logger.error(f"Error in forgot_password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing password reset request"
            )

    @staticmethod
    async def reset_password(reset_data: PasswordReset) -> dict:
        """
        Reset user password with token
        
        Args:
            reset_data (PasswordReset): Password reset data with token and new password
            
        Returns:
            dict: Response with success status
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in reset_password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error resetting password"
            )

    @staticmethod
    async def validate_token(user: dict) -> dict:
        """
        Validates the current user's token and returns user data
        
        Args:
            user (dict): User document from database (attached by middleware)
            
        Returns:
            dict: Response with user data
        """
        try:
            return {
                "success": True,
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "hasCompletedOnboarding": user.get("has_completed_onboarding", False),
                    "name": user.get("name"),
                    "company": user.get("company"),
                    "role": user.get("role"),
                    "roles": user.get("roles", ["user"])
                }
            }
        except Exception as e:
            logger.error(f"Error in validate_token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating token"
            )