from fastapi import APIRouter, HTTPException, Depends
from competitors.competitor_service import get_competitor_data, track_competitor, get_competitor_scraped_data
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

competitor_router = APIRouter()

@competitor_router.get("/")
def get_competitors(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch all competitors."""
    competitors = get_competitor_data(user)
    if not competitors:
        raise HTTPException(status_code=404, detail="No competitors found.")
    return competitors

@competitor_router.get("/{competitor_id}")
def get_competitor_by_id(competitor_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch specific competitor details."""
    competitor = get_competitor_data(competitor_id, user)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")
    return competitor

@competitor_router.post("/track")
def track_new_competitor(url: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Start tracking a competitor's website."""
    result = track_competitor(url, user)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to track competitor.")
    return {"message": "Competitor tracking started successfully."}

@competitor_router.get("/{competitor_id}/scraped-data")
def get_scraped_data(competitor_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch all scraped data for a specific competitor."""
    data = get_competitor_scraped_data(competitor_id, user)
    if not data:
        raise HTTPException(status_code=404, detail="No scraped data found.")
    return data
