# app/controllers/user_controller.py
from fastapi import HTTPException, status
from ..database import db
from datetime import datetime
from ..models.user import UserProfile
import logging

logger = logging.getLogger(__name__)

class UserController:
    @staticmethod
    async def get_user_state(user: dict) -> dict:
        """
        Get user's current state including onboarding and analysis status
        
        Args:
            user (dict): User document from database
            
        Returns:
            dict: User state information
            
        Raises:
            HTTPException: If user is not found
        """
        try:
            # Use _id instead of email for more efficient lookup
            user_id = user["_id"]
            user_data = await db.users.find_one({"_id": user_id})
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            analysis_status = user_data.get("analysis_status", "not_started")
            reports_status = "ready" if analysis_status == "complete" else "pending"

            return {
                "success": True,
                "state": {
                    "hasCompletedOnboarding": user_data.get("has_completed_onboarding", False),
                    "websiteUrl": user_data.get("website_url"),
                    "analysisStatus": analysis_status,
                    "reportsStatus": reports_status,
                    "lastUpdated": user_data.get("last_updated", user_data.get("created_at")),
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_user_state: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user state"
            )

    @staticmethod
    async def update_onboarding_status(user: dict, completed: bool) -> dict:
        """
        Update user's onboarding status
        
        Args:
            user (dict): User document from database
            completed (bool): Whether onboarding is completed
            
        Returns:
            dict: Success response
        """
        try:
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "has_completed_onboarding": completed,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Onboarding status updated successfully"
            }
        except Exception as e:
            logger.error(f"Error in update_onboarding_status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating onboarding status"
            )

    @staticmethod
    async def get_user_profile(user: dict) -> dict:
        """
        Get user's profile data
        
        Args:
            user (dict): User document from database
            
        Returns:
            dict: User profile data
            
        Raises:
            HTTPException: If user is not found
        """
        try:
            user_data = await db.users.find_one({"_id": user["_id"]})
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            profile = UserProfile(
                email=user_data["email"],
                name=user_data.get("name"),
                company=user_data.get("company"),
                role=user_data.get("role")
            )

            return {
                "success": True,
                "profile": profile.dict(exclude_unset=True)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_user_profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user profile"
            )
            
    @staticmethod
    async def update_profile(user_id: str, profile_data: UserProfile) -> dict:
        """
        Update user profile
        
        Args:
            user_id (str): User ID
            profile_data (UserProfile): Profile data to update
            
        Returns:
            dict: Updated user profile
            
        Raises:
            HTTPException: If user is not found
        """
        try:
            # Convert to dict and filter out None values
            update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
            
            if not update_data:
                # No update needed
                return await UserController.get_user_profile({"_id": user_id})
            
            # Add updated_at timestamp
            update_data["last_updated"] = datetime.utcnow()
            
            # Perform update
            result = await db.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get updated user
            return await UserController.get_user_profile({"_id": user_id})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user profile"
            )
    
    @staticmethod
    async def complete_onboarding(user_id: str, profile_data: UserProfile) -> dict:
        """
        Complete user onboarding by updating profile and setting has_completed_onboarding to True
        
        Args:
            user_id (str): User ID
            profile_data (UserProfile): Profile data to update
            
        Returns:
            dict: Updated user state
        """
        try:
            # Ensure has_completed_onboarding is set to True
            profile_data_dict = profile_data.dict(exclude_unset=True)
            
            # Update profile fields
            if profile_data_dict:
                await db.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            **profile_data_dict,
                            "has_completed_onboarding": True,
                            "last_updated": datetime.utcnow()
                        }
                    }
                )
            else:
                # Just update onboarding status if no profile data
                await db.users.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "has_completed_onboarding": True,
                            "last_updated": datetime.utcnow()
                        }
                    }
                )
            
            # Return updated state
            return await UserController.get_user_state({"_id": user_id})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in complete_onboarding: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error completing onboarding"
            )