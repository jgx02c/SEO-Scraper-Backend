# app/models/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    """User data for response"""
    id: str
    email: EmailStr
    name: Optional[str] = None
    hasCompletedOnboarding: bool = False
    company: Optional[str] = None
    role: Optional[str] = None
    roles: List[str] = ["user"]

class UserProfile(BaseModel):
    """User profile update model"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    has_completed_onboarding: Optional[bool] = None
    website_url: Optional[str] = None

class UserInDB(BaseModel):
    """User model as stored in database"""
    id: str
    email: EmailStr
    hashed_password: str
    name: Optional[str] = None
    has_completed_onboarding: bool = False
    company: Optional[str] = None
    role: Optional[str] = None
    roles: List[str] = ["user"]
    created_at: datetime
    updated_at: Optional[datetime] = None

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr

class PasswordReset(BaseModel):
    """Password reset model"""
    token: str
    new_password: str = Field(..., min_length=8)