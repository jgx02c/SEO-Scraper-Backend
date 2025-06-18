# app/routes/website.py
from fastapi import APIRouter, Depends, Request
from ..controllers.website_controller import WebsiteController
from ..dependencies import get_current_user
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Data"])
website_controller = WebsiteController()

@router.post("/analysis/start")
async def analyze_website(request: Request, data: dict, current_user: dict = Depends(get_current_user)):
    """
    DEPRECATED: Use /api/v2/websites/ endpoints instead.
    This endpoint is maintained for backward compatibility only.
    """
    logger.warning("DEPRECATED: /api/data/analysis/start is deprecated. Use /api/v2/websites/ instead.")
    
    # Start the analysis
    result = await website_controller.start_analysis(current_user, data.get("url"))
    
    # Create and track the background task
    background_task = asyncio.create_task(
        website_controller.run_analysis_tasks(
            analysis_id=result["analysis_id"],
            url=result["url"],
            user_email=current_user["email"]
        )
    )
    
    # Track the task using our app state
    request.app.track_background_task(background_task)
    
    return result

@router.get("/analysis/status")
async def get_analysis_status(current_user: dict = Depends(get_current_user)):
    """
    DEPRECATED: Use /api/v2/websites/ endpoints instead.
    This endpoint is maintained for backward compatibility only.
    """
    logger.warning("DEPRECATED: /api/data/analysis/status is deprecated. Use /api/v2/websites/ instead.")
    return await website_controller.get_analysis_status(current_user)