# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..database import supabase
from ..db.supabase import admin_supabase
import logging
from datetime import datetime
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
async def signup(user: UserCreate):
    """Register a new user"""
    try:
        # Create auth user
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "name": user.name,
                    "company": user.company,
                    "role": user.role
                }
            }
        })
        
        logger.info(f"Signup response: {auth_response}")
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Create user profile in the database
        profile_data = {
            "auth_user_id": auth_response.user.id,
            "email": user.email,
            "name": user.name,
            "company": user.company,
            "role": user.role,
            "has_completed_onboarding": False,
            "onboarding_step": 0,
            "plan_type": "free",
            "subscription_status": "active",
            "analyses_count": 0
        }
        
        try:
            profile_response = admin_supabase.table("user_profiles").insert(profile_data).execute()
            logger.info(f"Profile created successfully: {profile_response}")
        except Exception as profile_error:
            logger.error(f"Failed to create user profile: {str(profile_error)}")
            # If profile creation fails, we should still return success since auth user was created
            # The profile can be created later when they sign in
            pass
        
        return {
            "user": auth_response.user,
            "session": auth_response.session,
            "message": "User registered successfully. Please confirm your email if required."
        }
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/signin")
async def signin(user: UserLogin):
    """Authenticate user and return token with profile"""
    try:
        # Sign in user
        auth_response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        
        logger.info(f"Auth response received")
        
        # Note: Supabase gotrue-py client raises AuthApiError for invalid credentials,
        # so we handle that in the except block. We shouldn't see these checks trigger
        # for standard bad password flows.
        if not auth_response.user:
            logger.error("No user found in auth response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not auth_response.session:
            logger.error("No session found in auth response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No session created. Please check your email for verification."
            )
        
        # Get user profile
        profile_response = admin_supabase.table("user_profiles").select("*").eq("auth_user_id", auth_response.user.id).execute()
        
        profile = None
        if profile_response.data and isinstance(profile_response.data, list) and len(profile_response.data) > 0:
            profile = profile_response.data[0]
        else:
            # Create profile if it doesn't exist (for backward compatibility)
            logger.info(f"No profile found for user {auth_response.user.id}, creating one...")
            try:
                profile_data = {
                    "auth_user_id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": auth_response.user.user_metadata.get("name"),
                    "company": auth_response.user.user_metadata.get("company"),
                    "role": auth_response.user.user_metadata.get("role"),
                    "has_completed_onboarding": False,
                    "onboarding_step": 0,
                    "plan_type": "free",
                    "subscription_status": "active",
                    "analyses_count": 0
                }
                
                create_profile_response = admin_supabase.table("user_profiles").insert(profile_data).execute()
                if create_profile_response.data:
                    profile = create_profile_response.data[0]
                    logger.info(f"Profile created successfully during signin: {profile}")
            except Exception as profile_error:
                logger.error(f"Failed to create user profile during signin: {str(profile_error)}")
        
        response_data = {
            "user": auth_response.user,
            "profile": profile,
            "session": auth_response.session
        }
        
        logger.info(f"Returning response data with session")
        return response_data
        
    except AuthApiError as e:
        logger.error(f"Signin error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message or "Invalid login credentials"
        )
    except Exception as e:
        logger.error(f"A generic error occurred during signin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )

@router.post("/forgot-password")
async def forgot_password(email: str):
    """Request password reset"""
    try:
        response = supabase.auth.reset_password_email(email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password with token"""
    try:
        response = supabase.auth.verify_otp({
            "token_hash": token,
            "type": "recovery"
        })
        return {"message": "Password reset successful"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

