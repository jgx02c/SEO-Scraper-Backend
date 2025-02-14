from fastapi import APIRouter, HTTPException, Depends
from actions.actions_service import create_report_action, scrape_website_action, run_ai_agent_action
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

actions_router = APIRouter()

@actions_router.post("/create-report")
def create_report_action_route(report_type: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Trigger a new report creation action (SEO, traffic, competitor, etc.)."""
    result = create_report_action(report_type, user)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create report.")
    return {"message": "Report creation triggered successfully."}

@actions_router.post("/scrape-website")
def scrape_website_action_route(url: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Start a website scrape action."""
    result = scrape_website_action(url, user)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to scrape website.")
    return {"message": "Website scraping started successfully."}

@actions_router.post("/run-ai-agent")
def run_ai_agent_action_route(action_type: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Trigger AI agent to perform actions like SEO fixes or content generation."""
    result = run_ai_agent_action(action_type, user)
    if not result:
        raise HTTPException(status_code=400, detail="AI action failed.")
    return {"message": "AI action executed successfully."}
