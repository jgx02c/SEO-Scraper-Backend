# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..database import supabase
import logging
from datetime import datetime

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
        
        # We'll create the profile when the user signs in instead
        # This avoids foreign key constraint issues
        
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
        
        logger.info(f"Auth response received: {auth_response}")
        
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
        profile_response = supabase.table("user_profiles").select("*").eq("id", auth_response.user.id).execute()
        
        # Just return the profile if it exists, don't try to create one
        response_data = {
            "user": auth_response.user,
            "profile": profile_response.data[0] if profile_response.data and isinstance(profile_response.data, list) else None,
            "session": auth_response.session
        }
        
        logger.info(f"Returning response data with session: {auth_response.session}")
        return response_data
        
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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

