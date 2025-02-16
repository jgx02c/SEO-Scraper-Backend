# app/controllers/user_controller.py
from ..dependencies import db
from datetime import datetime

class UserController:
    @staticmethod
    async def get_user_state(user: dict) -> dict:
        return {
            "hasCompletedOnboarding": user.get("has_completed_onboarding", False),
            "reportsGenerated": user.get("reports_generated", False)
        }

    @staticmethod
    async def update_website_url(user: dict, url: str) -> dict:
        await db.users.update_one(
            {"email": user["email"]},
            {
                "$set": {
                    "website_url": url,
                    "analysis_started": datetime.utcnow(),
                    "analysis_status": "processing"
                }
            }
        )
        return {"message": "Website URL updated and analysis started"}