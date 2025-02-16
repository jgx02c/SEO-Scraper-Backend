# app/controllers/website_controller.py
from fastapi import HTTPException, status
from ..dependencies import db
from datetime import datetime
from urllib.parse import urlparse

class WebsiteController:
    @staticmethod
    async def start_analysis(user: dict, url: str) -> dict:
        # Validate URL
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL provided"
            )

        try:
            await db.users.update_one(
                {"email": user["email"]},
                {
                    "$set": {
                        "website_url": url,
                        "analysis_started": datetime.utcnow(),
                        "analysis_status": "processing",
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Here you would trigger your actual analysis process
            return {
                "success": True,
                "message": "Analysis started",
                "url": url,
                "status": "processing"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start analysis: {str(e)}"
            )

    @staticmethod
    async def get_analysis_status(user: dict) -> dict:
        try:
            current_user = await db.users.find_one({"email": user["email"]})
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return {
                "success": True,
                "status": current_user.get("analysis_status", "not_started"),
                "website_url": current_user.get("website_url"),
                "last_updated": current_user.get("last_updated", current_user.get("created_at")),
                "isComplete": current_user.get("analysis_status") == "complete"
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analysis status: {str(e)}"
            )