from fastapi import APIRouter, HTTPException, Depends
from business.business_service import get_business_data, track_business, get_scraped_business_data
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

business_router = APIRouter()

@business_router.get("/")
def get_businesses(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch all businesses."""
    businesses = get_business_data(user)
    if not businesses:
        raise HTTPException(status_code=404, detail="No businesses found.")
    return businesses

@business_router.get("/{business_id}")
def get_business_by_id(business_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch specific business details."""
    business = get_business_data(business_id, user)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")
    return business

@business_router.post("/track")
def track_new_business(url: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Start tracking a business for scraping."""
    result = track_business(url, user)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to track business.")
    return {"message": "Business tracking started successfully."}

@business_router.get("/{business_id}/scraped-data")
def get_business_scraped_data(business_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch all scraped data for a specific business."""
    data = get_scraped_business_data(business_id, user)
    if not data:
        raise HTTPException(status_code=404, detail="No scraped data found.")
    return data
