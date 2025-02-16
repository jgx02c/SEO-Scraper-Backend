# app/models/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = datetime.utcnow()
    has_completed_onboarding: bool = False
    website_url: Optional[str] = None
    analysis_status: Optional[str] = None
    reports_generated: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None