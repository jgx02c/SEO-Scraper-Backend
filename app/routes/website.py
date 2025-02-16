# app/routes/website.py
from fastapi import APIRouter, Depends, Body
from ..controllers.website_controller import WebsiteController
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/website", tags=["website"])

@router.post("/analyze")
async def analyze_website(url: str = Body(...), current_user: dict = Depends(get_current_user)):
    return await WebsiteController.start_analysis(current_user, url)

@router.get("/status")
async def get_analysis_status(current_user: dict = Depends(get_current_user)):
    return await WebsiteController.get_analysis_status(current_user)