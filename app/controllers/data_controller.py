# app/controllers/data_controller.py
from fastapi import HTTPException, status
from ..database import db  # Keep for reports
from ..utils.supabase import get_analysis_by_user_id, create_analysis, update_analysis
import logging

logger = logging.getLogger(__name__)

class DataController:
    """Controller for handling data and analysis operations"""
    
    @staticmethod
    async def get_analysis_data(user_id: str) -> dict:
        """
        Get analysis data for a user from Supabase
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            dict: Analysis data
        """
        try:
            # Get analysis data from Supabase
            analysis_data = await get_analysis_by_user_id(user_id)
            
            # If no analysis data exists yet
            if not analysis_data:
                return {
                    "success": True,
                    "data": None,
                    "message": "No analysis data available"
                }
            
            return {
                "success": True,
                "data": analysis_data
            }
        except Exception as e:
            logger.error(f"Error retrieving analysis data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving analysis data"
            )
    
    @staticmethod
    async def update_analysis_data(user_id: str, analysis_data: dict) -> dict:
        """
        Update analysis data for a user in Supabase
        
        Args:
            user_id (str): ID of the user
            analysis_data (dict): Analysis data to update
            
        Returns:
            dict: Updated analysis data
        """
        try:
            # Check if analysis data exists
            existing_data = await get_analysis_by_user_id(user_id)
            
            if existing_data:
                # Update existing analysis data
                updated_data = await update_analysis(user_id, analysis_data)
            else:
                # Create new analysis data
                analysis_data["user_id"] = user_id
                updated_data = await create_analysis(analysis_data)
            
            return {
                "success": True,
                "data": updated_data
            }
        except Exception as e:
            logger.error(f"Error updating analysis data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating analysis data"
            )
    
    @staticmethod
    async def start_analysis(user_id: str, website_url: str) -> dict:
        """
        Start a new website analysis
        
        Args:
            user_id (str): ID of the user
            website_url (str): URL of the website to analyze
            
        Returns:
            dict: Response with success status
        """
        try:
            # Update user with website URL and analysis status
            await db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "website_url": website_url,
                        "analysis_status": "pending"
                    }
                }
            )
            
            # Create analysis record
            analysis = {
                "user_id": user_id,
                "website_url": website_url,
                "status": "pending",
                "created_at": db.get_current_time(),
                "updated_at": db.get_current_time()
            }
            
            # Upsert analysis record
            await db.analysis.update_one(
                {"user_id": user_id},
                {"$set": analysis},
                upsert=True
            )
            
            # Here you would typically start the analysis as a background task
            # For example:
            # analysis_task = asyncio.create_task(run_analysis(user_id, website_url))
            # app.track_background_task(analysis_task)
            
            return {
                "success": True,
                "message": "Analysis started successfully"
            }
        except Exception as e:
            logger.error(f"Error starting analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error starting analysis"
            )
    
    @staticmethod
    async def get_analysis_status(user_id: str) -> dict:
        """
        Get the status of a user's website analysis
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            dict: Analysis status information
        """
        try:
            user = await db.users.find_one({"_id": user_id})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            analysis_status = user.get("analysis_status", "not_started")
            
            return {
                "success": True,
                "status": analysis_status,
                "websiteUrl": user.get("website_url")
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving analysis status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving analysis status"
            )