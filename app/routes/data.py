# app/routes/data.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..controllers.data_controller import DataController
from ..dependencies import get_current_user
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["Data"])

class WebsiteAnalysisRequest(BaseModel):
    website_url: str

@router.get("/analysis")
async def get_analysis_data(request: Request):
    """Get user's analysis data"""
    try:
        current_user = await get_current_user(request)
        return await DataController.get_analysis_data(current_user["_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_analysis_data route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analysis data"
        )

@router.post("/analysis/start")
async def start_analysis(analysis_request: WebsiteAnalysisRequest, request: Request):
    """Start a new website analysis"""
    try:
        current_user = await get_current_user(request)
        return await DataController.start_analysis(
            current_user["_id"], 
            analysis_request.website_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in start_analysis route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting analysis"
        )

@router.get("/analysis/status")
async def get_analysis_status(request: Request):
    """Get the status of the current analysis"""
    try:
        current_user = await get_current_user(request)
        return await DataController.get_analysis_status(current_user["_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_analysis_status route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analysis status"
        )