from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional
from ..controllers.v2 import (
    WebsiteController, SnapshotController, 
    ComparisonController, CompetitorController, ScanController
)
from ..models.website import (
    Website, WebsiteSnapshot, SnapshotComparison,
    WebsiteCreateRequest, SnapshotCreateRequest, ComparisonRequest,
    WebsiteType, WebsiteListResponse, SnapshotListResponse
)
from ..database import db
import logging
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/websites", 
    tags=["Websites V2"]
)

# Initialize controllers
website_controller = WebsiteController()
snapshot_controller = SnapshotController()
comparison_controller = ComparisonController()
competitor_controller = CompetitorController()
scan_controller = ScanController()

# ===== SCAN INITIATION =====

class ScanInitiateRequest(BaseModel):
    url: HttpUrl
    name: Optional[str] = None

@router.post("/scans/initiate", response_model=WebsiteSnapshot)
async def initiate_scan(
    request: Request,
    scan_request: ScanInitiateRequest
):
    """
    Initiates a scan for a website.
    This is the primary entry point for starting a new analysis.
    It will automatically create a 'MAIN' website record if one
    does not already exist for the user, and then create a new
    snapshot to start the scan.
    """
    try:
        snapshot = await scan_controller.start_initial_scan(
            request, 
            str(scan_request.url),
            scan_request.name
        )
        return snapshot
    except Exception as e:
        logger.error(f"Error in initiate_scan route: {str(e)}")
        # The controller already raises HTTPException, but this is a fallback
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate scan"
        )

# ===== WEBSITE MANAGEMENT =====

@router.post("/", response_model=Website)
async def create_website(
    request: Request,
    create_request: WebsiteCreateRequest
):
    """Create a new master website record"""
    try:
        return await website_controller.create_website(request, create_request)
    except Exception as e:
        logger.error(f"Error in create_website route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating website"
        )

@router.get("/", response_model=WebsiteListResponse)
async def list_websites(
    request: Request,
    website_type: Optional[WebsiteType] = Query(None, description="Filter by website type")
):
    """Get all websites for the current user"""
    try:
        websites = await website_controller.get_user_websites(request, website_type)
        return WebsiteListResponse(websites=websites, total=len(websites))
    except Exception as e:
        logger.error(f"Error in list_websites route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving websites"
        )

@router.get("/{website_id}", response_model=Website)
async def get_website(
    request: Request,
    website_id: str
):
    """Get a specific website by ID"""
    try:
        return await website_controller.get_website(request, website_id)
    except Exception as e:
        logger.error(f"Error in get_website route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving website"
        )

# ===== SNAPSHOT MANAGEMENT =====

@router.post("/snapshots", response_model=WebsiteSnapshot)
async def create_snapshot(
    request: Request,
    create_request: SnapshotCreateRequest
):
    """Create a new snapshot for a website"""
    try:
        return await snapshot_controller.create_snapshot(request, create_request)
    except Exception as e:
        logger.error(f"Error in create_snapshot route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating snapshot"
        )

@router.get("/{website_id}/snapshots", response_model=SnapshotListResponse)
async def list_snapshots(
    request: Request,
    website_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of snapshots to return")
):
    """Get snapshots for a website"""
    try:
        snapshots = await snapshot_controller.get_website_snapshots(
            request, website_id, limit
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
    request: Request,
    snapshot_id: str
):
    """Get a specific snapshot by ID"""
    try:
        return await snapshot_controller.get_snapshot(request, snapshot_id)
    except Exception as e:
        logger.error(f"Error in get_snapshot route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshot"
        )

@router.get("/snapshots/current/status")
async def get_current_snapshot_status(request: Request):
    """Get the status of the most recent snapshot for the user (for long polling during sign-up)"""
    try:
        user = request.state.user
        # First try to find any in-progress snapshot
        in_progress_snapshot = await db.website_snapshots.find_one(
            {
                "user_id": user["id"],
                "scan_status": {"$in": ["pending", "crawling", "scanning", "generating_report"]}
            },
            sort=[("started_at", -1)]
        )
        
        if in_progress_snapshot:
            return {
                "success": True,
                "status": in_progress_snapshot["scan_status"],
                "current_step": in_progress_snapshot["current_step"],
                "pages_discovered": in_progress_snapshot.get("pages_discovered", 0),
                "pages_scraped": in_progress_snapshot.get("pages_scraped", 0),
                "pages_failed": in_progress_snapshot.get("pages_failed", 0),
                "snapshot_id": str(in_progress_snapshot["_id"]),
                "website_id": str(in_progress_snapshot["website_id"]),
                "base_url": in_progress_snapshot["base_url"]
            }
        
        # If no in-progress, get the most recent completed snapshot
        latest_snapshot = await db.website_snapshots.find_one(
            {"user_id": user["id"]},
            sort=[("started_at", -1)]
        )
        
        if not latest_snapshot:
            return {
                "success": True,
                "status": "not_started"
            }
        
        return {
            "success": True,
            "status": latest_snapshot["scan_status"],
            "current_step": latest_snapshot["current_step"],
            "pages_discovered": latest_snapshot.get("pages_discovered", 0),
            "pages_scraped": latest_snapshot.get("pages_scraped", 0),
            "pages_failed": latest_snapshot.get("pages_failed", 0),
            "snapshot_id": str(latest_snapshot["_id"]),
            "website_id": str(latest_snapshot["website_id"]),
            "base_url": latest_snapshot["base_url"],
            "completed_at": latest_snapshot.get("completed_at")
        }
        
    except Exception as e:
        logger.error(f"Error in get_current_snapshot_status route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshot status"
        )

# ===== COMPARISON & ANALYSIS =====

@router.post("/compare", response_model=SnapshotComparison)
async def compare_snapshots(
    request: Request,
    comparison_request: ComparisonRequest
):
    """Compare two snapshots to detect changes"""
    try:
        return await comparison_controller.compare_snapshots(request, comparison_request)
    except Exception as e:
        logger.error(f"Error in compare_snapshots route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error comparing snapshots"
        )

# ===== COMPETITOR MANAGEMENT =====

@router.get("/competitors", response_model=WebsiteListResponse)
async def list_competitors(request: Request):
    """Get all competitor websites for the current user"""
    try:
        competitors = await competitor_controller.get_competitors(request)
        return WebsiteListResponse(websites=competitors, total=len(competitors))
    except Exception as e:
        logger.error(f"Error in list_competitors route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving competitors"
        )

@router.post("/competitors", response_model=Website)
async def add_competitor(
    request: Request,
    create_request: WebsiteCreateRequest
):
    """Add a new competitor website"""
    try:
        return await competitor_controller.add_competitor(request, create_request)
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
    request: Request,
    website_id: str
):
    """Analyze a website against all competitors"""
    try:
        return await competitor_controller.analyze_against_competitors(
            request, website_id
        )
    except Exception as e:
        logger.error(f"Error getting competitive analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing competitive analysis"
        )

@router.get("/{website_id}/comparisons")
async def get_website_comparisons(
    request: Request,
    website_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of comparisons to return")
):
    """Get comparison history for a website"""
    try:
        comparisons = await comparison_controller.get_website_comparisons(
            request, website_id, limit
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
    request: Request,
    snapshot_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of pages to return")
):
    """Get pages for a specific snapshot"""
    try:
        pages = await snapshot_controller.get_snapshot_pages(
            request, snapshot_id, limit
        )
        return {"pages": pages, "total": len(pages)}
    except Exception as e:
        logger.error(f"Error in get_snapshot_pages route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving snapshot pages"
        )

@router.get("/dashboard/summary")
async def get_dashboard_summary(request: Request):
    """Get summary data for the dashboard"""
    try:
        user = request.state.user
        # Get all websites
        all_websites = await website_controller.get_user_websites(request)
        
        # Separate by type
        primary_sites = [w for w in all_websites if w.website_type == WebsiteType.MAIN]
        competitors = [w for w in all_websites if w.website_type == WebsiteType.COMPETITOR]
        
        # Get latest snapshot for top primary sites
        summary_data = {
            "total_websites": len(all_websites),
            "primary_websites": len(primary_sites),
            "competitors": len(competitors),
            "total_snapshots": sum(w.total_snapshots for w in all_websites),
            "primary_snapshots": [],
            "websites": all_websites
        }
        for website in primary_sites[:3]:  # Limit to top 3 for performance
            snapshots = await snapshot_controller.get_website_snapshots(
                request, str(website.id), limit=1
            )
            if snapshots:
                summary_data["primary_snapshots"].append(snapshots[0])
        
        return summary_data
    except Exception as e:
        logger.error(f"Error in get_dashboard_summary route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dashboard summary"
        ) 