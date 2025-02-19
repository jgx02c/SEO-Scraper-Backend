# app/routes/website.py
from fastapi import APIRouter, Depends, Request
from ..controllers.website_controller import WebsiteController
from ..dependencies import get_current_user
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/website")

@router.post("/analyze")
async def analyze_website(request: Request, data: dict, current_user: dict = Depends(get_current_user)):
    # Start the analysis
    result = await WebsiteController.start_analysis(current_user, data.get("url"))
    
    # Create and track the background task
    background_task = asyncio.create_task(
        WebsiteController.run_analysis_tasks(
            business_id=result["business_id"],
            url=result["url"],
            user_email=current_user["email"]
        )
    )
    
    # Track the task using our app state
    request.app.track_background_task(background_task)
    
    return result

@router.get("/status")
async def get_analysis_status(current_user: dict = Depends(get_current_user)):
    return await WebsiteController.get_analysis_status(current_user)