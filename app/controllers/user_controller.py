# app/controllers/user_controller.py
from fastapi import HTTPException, status
from ..dependencies import db
from datetime import datetime

class UserController:
    @staticmethod
    async def get_user_state(user: dict) -> dict:
        user_data = await db.users.find_one({"email": user["email"]})
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

    @staticmethod
    async def update_onboarding_status(user: dict, completed: bool) -> dict:
        await db.users.update_one(
            {"email": user["email"]},
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