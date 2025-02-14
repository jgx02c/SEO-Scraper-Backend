from fastapi import APIRouter, HTTPException, Depends
from ai.ai_service import generate_seo_fixes, run_ai_action
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

ai_router = APIRouter()

@ai_router.post("/seo-fix")
def fix_seo_issues(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Trigger AI to automatically fix SEO issues (e.g., broken links, missing alt text)."""
    result = generate_seo_fixes(user)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to apply AI fixes.")
    return {"message": "AI fixes applied successfully."}

@ai_router.post("/run-action")
def trigger_ai_action(action: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Run a specific AI action (e.g., competitor analysis, content generation)."""
    result = run_ai_action(action, user)
    if not result:
        raise HTTPException(status_code=400, detail="AI action failed.")
    return {"message": f"AI action '{action}' executed successfully."}
