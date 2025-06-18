from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..controllers.v2 import (
    WebsiteController, SnapshotController, 
    ComparisonController, CompetitorController
)
from ..dependencies import get_current_user
from ..models.website import (
    Website, WebsiteSnapshot, SnapshotComparison,
    WebsiteCreateRequest, SnapshotCreateRequest, ComparisonRequest,
    WebsiteType, WebsiteListResponse, SnapshotListResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/websites", tags=["Websites V2"])

# Initialize controllers
website_controller = WebsiteController()
snapshot_controller = SnapshotController()
comparison_controller = ComparisonController()
competitor_controller = CompetitorController()

# ===== WEBSITE MANAGEMENT =====

@router.post("/", response_model=Website)
async def create_website(
    request: WebsiteCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new master website record"""
    try:
        return await website_controller.create_website(current_user["id"], request)
    except Exception as e:
        logger.error(f"Error in create_website route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating website"
        )

@router.get("/", response_model=WebsiteListResponse)
async def list_websites(
    website_type: Optional[WebsiteType] = Query(None, description="Filter by website type"),
    current_user: dict = Depends(get_current_user)
):
    """Get all websites for the current user"""
    try:
        websites = await website_controller.get_user_websites(current_user["id"], website_type)
        return WebsiteListResponse(websites=websites, total=len(websites))
    except Exception as e:
        logger.error(f"Error in list_websites route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving websites"
        )

@router.get("/{website_id}", response_model=Website)
async def get_website(
    website_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific website by ID"""
    try:
        return await website_controller.get_website(current_user["id"], website_id)
    except Exception as e:
        logger.error(f"Error in get_website route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving website"
        )

# ===== SNAPSHOT MANAGEMENT =====

@router.post("/snapshots", response_model=WebsiteSnapshot)
async def create_snapshot(
    request: SnapshotCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new snapshot for a website"""
    try:
        return await snapshot_controller.create_snapshot(current_user["id"], request)
    except Exception as e:
        logger.error(f"Error in create_snapshot route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating snapshot"
        )

@router.get("/{website_id}/snapshots", response_model=SnapshotListResponse)
async def list_snapshots(
    website_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of snapshots to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get snapshots for a website"""
    try:
        snapshots = await snapshot_controller.get_website_snapshots(
            current_user["id"], website_id, limit
        )
        return SnapshotListResponse(snapshots=snapshots, total=len(snapshots))
    except Exception as e:
        logger.error(f"Error in list_snapshots route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshots"
        )

@router.get("/snapshots/{snapshot_id}", response_model=WebsiteSnapshot)
async def get_snapshot(
    snapshot_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific snapshot by ID"""
    try:
        return await snapshot_controller.get_snapshot(current_user["id"], snapshot_id)
    except Exception as e:
        logger.error(f"Error in get_snapshot route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshot"
        )

# ===== COMPARISON & ANALYSIS =====

@router.post("/compare", response_model=SnapshotComparison)
async def compare_snapshots(
    request: ComparisonRequest,
    current_user: dict = Depends(get_current_user)
):
    """Compare two snapshots to detect changes"""
    try:
        return await comparison_controller.compare_snapshots(current_user["id"], request)
    except Exception as e:
        logger.error(f"Error in compare_snapshots route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing snapshots"
        )

# ===== COMPETITOR MANAGEMENT =====

@router.get("/competitors", response_model=WebsiteListResponse)
async def list_competitors(
    current_user: dict = Depends(get_current_user)
):
    """Get all competitor websites for the current user"""
    try:
        competitors = await competitor_controller.get_competitors(current_user["id"])
        return WebsiteListResponse(websites=competitors, total=len(competitors))
    except Exception as e:
        logger.error(f"Error in list_competitors route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving competitors"
        )

@router.post("/competitors", response_model=Website)
async def add_competitor(
    request: WebsiteCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a new competitor website"""
    try:
        return await competitor_controller.add_competitor(current_user["id"], request)
    except Exception as e:
        logger.error(f"Error in add_competitor route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding competitor"
        )

# ===== DASHBOARD DATA =====

# ===== COMPETITIVE ANALYSIS =====

@router.get("/{website_id}/competitive-analysis")
async def get_competitive_analysis(
    website_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Analyze a website against all competitors"""
    try:
        return await competitor_controller.analyze_against_competitors(
            current_user["id"], website_id
        )
    except Exception as e:
        logger.error(f"Error in get_competitive_analysis route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing competitive analysis"
        )

@router.get("/{website_id}/comparisons")
async def get_website_comparisons(
    website_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of comparisons to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get comparison history for a website"""
    try:
        comparisons = await comparison_controller.get_website_comparisons(
            current_user["id"], website_id, limit
        )
        return {"comparisons": comparisons, "total": len(comparisons)}
    except Exception as e:
        logger.error(f"Error in get_website_comparisons route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving comparisons"
        )

@router.get("/snapshots/{snapshot_id}/pages")
async def get_snapshot_pages(
    snapshot_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of pages to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get pages for a specific snapshot"""
    try:
        pages = await snapshot_controller.get_snapshot_pages(
            current_user["id"], snapshot_id, limit
        )
        return {"pages": pages, "total": len(pages)}
    except Exception as e:
        logger.error(f"Error in get_snapshot_pages route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshot pages"
        )

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get summary data for the dashboard"""
    try:
        # Get all websites
        all_websites = await website_controller.get_user_websites(current_user["id"])
        
        # Separate by type
        primary_sites = [w for w in all_websites if w.website_type == WebsiteType.PRIMARY]
        competitors = [w for w in all_websites if w.website_type == WebsiteType.COMPETITOR]
        
        # Get recent snapshots for primary sites
        recent_snapshots = []
        for website in primary_sites[:3]:  # Limit to top 3 for performance
            snapshots = await snapshot_controller.get_website_snapshots(
                current_user["id"], str(website.id), limit=1
            )
            if snapshots:
                recent_snapshots.extend(snapshots)
        
        return {
            "total_websites": len(all_websites),
            "primary_websites": len(primary_sites),
            "competitors": len(competitors),
            "total_snapshots": sum(w.total_snapshots for w in all_websites),
            "recent_snapshots": recent_snapshots,
            "websites": all_websites
        }
    except Exception as e:
        logger.error(f"Error in get_dashboard_summary route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dashboard summary"
        ) 