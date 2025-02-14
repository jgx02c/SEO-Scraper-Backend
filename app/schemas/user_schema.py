from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base schema for common user fields
class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Schema for user registration (includes password)
class UserRegister(UserBase):
    password: str

# Schema for logging in (only email and password required)
class UserLogin(BaseModel):
    email: str
    password: str

# Schema for user creation (could be used for creating or updating a user)
class UserCreate(UserBase):
    password: str

# Schema for responding with User data (for API responses)
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # This tells Pydantic to treat SQLAlchemy models as dictionaries
