# app/routes/report.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..controllers.website_controller import WebsiteController
from ..dependencies import get_current_user
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["Data"])
website_controller = WebsiteController()

class WebsiteAnalysisRequest(BaseModel):
    website_url: str

@router.get("/{analysis_id}")
async def get_report(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """
    DEPRECATED: Use /api/v2/websites/ endpoints instead.
    This endpoint is maintained for backward compatibility only.
    """
    logger.warning("DEPRECATED: /api/report/{analysis_id} is deprecated. Use /api/v2/websites/ instead.")
    try:
        return await website_controller.get_analysis_report(analysis_id, current_user)
    except Exception as e:
        logger.error(f"Error in get_report route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analysis report"
        )