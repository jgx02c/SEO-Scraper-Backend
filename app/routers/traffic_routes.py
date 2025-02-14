from fastapi import APIRouter, HTTPException, Depends
from traffic.traffic_service import get_website_traffic, get_social_traffic, get_ads_traffic
from traffic.analytics_service import get_seo_performance, get_user_behavior, get_competitor_comparison
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

traffic_router = APIRouter()

@traffic_router.get("/website")
def get_website_traffic_data(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch website traffic data (page views, sessions, etc.)."""
    traffic_data = get_website_traffic(user)
    if not traffic_data:
        raise HTTPException(status_code=404, detail="No website traffic data found.")
    return traffic_data

@traffic_router.get("/social")
def get_social_traffic_data(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch social media traffic data (Instagram, Twitter, etc.)."""
    traffic_data = get_social_traffic(user)
    if not traffic_data:
        raise HTTPException(status_code=404, detail="No social traffic data found.")
    return traffic_data

@traffic_router.get("/ads")
def get_ads_performance(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch ad performance data (Google Ads, Meta Ads, etc.)."""
    ads_data = get_ads_traffic(user)
    if not ads_data:
        raise HTTPException(status_code=404, detail="No ads data found.")
    return ads_data

@traffic_router.get("/seo-performance")
def get_seo_performance_data(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch SEO performance data (keywords, backlinks, page speed, etc.)."""
    seo_data = get_seo_performance(user)
    if not seo_data:
        raise HTTPException(status_code=404, detail="No SEO performance data found.")
    return seo_data

@traffic_router.get("/user-behavior")
def get_user_behavior_data(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Fetch user behavior data (heatmaps, conversion funnels, etc.)."""
    user_behavior_data = get_user_behavior(user)
    if not user_behavior_data:
        raise HTTPException(status_code=404, detail="No user behavior data found.")
    return user_behavior_data

@traffic_router.get("/competitor-comparison")
def compare_with_competitors(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Compare your performance with competitors."""
    competitor_data = get_competitor_comparison(user)
    if not competitor_data:
        raise HTTPException(status_code=404, detail="No competitor comparison data found.")
    return competitor_data
