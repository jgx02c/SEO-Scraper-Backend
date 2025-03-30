# app/controllers/auth_controller.py
from fastapi import HTTPException, status
from ..models.user import UserCreate, UserLogin, UserInDB, Token, PasswordResetRequest, PasswordReset
from ..utils.jwt_handler import create_access_token
from ..utils.security import verify_password, get_password_hash
from ..utils.supabase import create_user, get_user_by_email, update_user
from ..database import db  # Keep for reports
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)

class AuthController:
    @staticmethod
    async def signup(user: UserCreate) -> dict:
        """
        Register a new user using Supabase Auth
        
        Args:
            user (UserCreate): User registration data
            
        Returns:
            dict: Response with token and user data
            
        Raises:
            HTTPException: If email already exists
        """
        try:
            # Check if user exists
            existing_user = await get_user_by_email(user.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Create user in Supabase Auth
            user_data = UserInDB(
                email=user.email,
                hashed_password=get_password_hash(user.password),
                created_at=datetime.utcnow(),
                roles=["user"]
            )
            
            # Create user in Supabase
            new_user = await create_user(user_data.dict())
            
            # Create access token with user ID and roles
            token_data = {
                "sub": user.email,
                "user_id": new_user["id"],
                "roles": ["user"]
            }
            access_token = create_access_token(data=token_data)
            
            # Return both token and user data
            return {
                "success": True,
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": new_user["id"],
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
        Sign in user using Supabase Auth
        
        Args:
            user (UserLogin): User login data
            
        Returns:
            dict: Response with token and user data
        """
        try:
            # Get user from Supabase
            db_user = await get_user_by_email(user.email)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Verify password
            if not verify_password(user.password, db_user["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Create access token
            token_data = {
                "sub": db_user["email"],
                "user_id": db_user["id"],
                "roles": db_user.get("roles", ["user"])
            }
            access_token = create_access_token(data=token_data)
            
            return {
                "success": True,
                "token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": db_user["id"],
                    "email": db_user["email"],
                    "hasCompletedOnboarding": db_user.get("hasCompletedOnboarding", False),
                    "roles": db_user.get("roles", ["user"])
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in signin: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error signing in"
            )

    @staticmethod
    async def forgot_password(request: PasswordResetRequest) -> dict:
        """
        Initiate password reset process using Supabase Auth
        
        Args:
            request (PasswordResetRequest): Password reset request with email
            
        Returns:
            dict: Response with success status
        """
        try:
            user = await get_user_by_email(request.email)
            if not user:
                # Return success even if user doesn't exist for security
                return {
                    "success": True,
                    "message": "If an account exists with this email, you will receive a password reset link"
                }
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            
            # Store reset token in Supabase
            await update_user(user["id"], {
                "reset_token": reset_token,
                "reset_token_expires": reset_token_expires
            })
            
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