# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..models.user import UserCreate, UserLogin, PasswordResetRequest, PasswordReset
from ..controllers.auth_controller import AuthController
from ..dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(user: UserCreate):
    """Register a new user"""
    return await AuthController.signup(user)

@router.post("/signin")
async def signin(user: UserLogin):
    """Authenticate user and return token"""
    return await AuthController.signin(user)

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset"""
    return await AuthController.forgot_password(request)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password with token"""
    return await AuthController.reset_password(reset_data)

@router.get("/me")
async def me(request: Request):
    """Get current user profile"""
    try:
        current_user = await get_current_user(request)
        return await AuthController.validate_token(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )