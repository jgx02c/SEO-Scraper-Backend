# app/routes/website.py
from fastapi import APIRouter, Depends, Body
from ..controllers.website_controller import WebsiteController
from ..dependencies import get_current_user
from pydantic import BaseModel

class WebsiteURLRequest(BaseModel):
    url: str

router = APIRouter(prefix="/api/website", tags=["website"])

@router.post("/analyze")
async def analyze_website(
    request: WebsiteURLRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    return await WebsiteController.start_analysis(current_user, request.url)

@router.get("/status")
async def get_analysis_status(current_user: dict = Depends(get_current_user)):
    return await WebsiteController.get_analysis_status(current_user)