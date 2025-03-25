# app/routes/user.py
from fastapi import APIRouter, HTTPException, status, Request
from ..models.user import UserProfile
from ..controllers.user_controller import UserController
from ..dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/state")
async def get_user_state(request: Request):
    """Get user's current state"""
    try:
        current_user = await get_current_user(request)
        return await UserController.get_user_state(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_state route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user state"
        )

@router.post("/onboarding")
async def update_onboarding(completed: bool, request: Request):
    """Update user's onboarding status"""
    try:
        current_user = await get_current_user(request)
        return await UserController.update_onboarding_status(current_user, completed)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_onboarding route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating onboarding status"
        )

@router.get("/profile")
async def get_profile(request: Request):
    """Get user profile"""
    try:
        current_user = await get_current_user(request)
        return await UserController.get_user_profile(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_profile route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

@router.put("/profile")
async def update_profile(profile_data: UserProfile, request: Request):
    """Update user profile"""
    try:
        current_user = await get_current_user(request)
        return await UserController.update_profile(current_user["_id"], profile_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_profile route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )

@router.post("/complete-onboarding")
async def complete_onboarding(profile_data: UserProfile, request: Request):
    """Complete user onboarding with profile data"""
    try:
        current_user = await get_current_user(request)
        return await UserController.complete_onboarding(current_user["_id"], profile_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_onboarding route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error completing onboarding"
        )