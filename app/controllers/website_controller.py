# app/controllers/website_controller.py
from ..dependencies import db
from datetime import datetime

class WebsiteController:
    @staticmethod
    async def start_analysis(user: dict, url: str) -> dict:
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
        # Here you would trigger your actual analysis process
        return {"message": "Analysis started"}

    @staticmethod
    async def get_analysis_status(user: dict) -> dict:
        current_user = await db.users.find_one({"email": user["email"]})
        return {
            "isComplete": current_user.get("analysis_status") == "complete",
            "status": current_user.get("analysis_status", "not_started")
        }