"""
Snapshot Controller V2

Handles snapshot creation, management, and scanning operations.
Focused on website snapshots without comparison logic.
"""

from fastapi import HTTPException, status
from ...database import db
from ...models.website import (
    WebsiteSnapshot, PageSnapshot, SnapshotCreateRequest,
    ScanStatus, PyObjectId
)
from .website_controller import WebsiteController
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any
import asyncio
import logging
import hashlib

logger = logging.getLogger(__name__)

class SnapshotController:
    """Controller for snapshot operations"""
    
    def __init__(self):
        self.snapshots_collection = db.website_snapshots
        self.pages_collection = db.page_snapshots
        self.website_controller = WebsiteController()
        
    async def create_snapshot(self, user_id: str, request: SnapshotCreateRequest) -> WebsiteSnapshot:
        """Create a new snapshot for a website"""
        try:
            # Get the website record
            website = await self.website_controller.get_website(user_id, request.website_id)
            
            # Get the next version number
            latest_snapshot = await self.snapshots_collection.find_one(
                {"website_id": PyObjectId(request.website_id)},
                sort=[("version", -1)]
            )
            next_version = (latest_snapshot["version"] + 1) if latest_snapshot else 1
            
            # Create snapshot document
            snapshot_doc = {
                "website_id": PyObjectId(request.website_id),
                "user_id": user_id,
                "snapshot_date": datetime.utcnow(),
                "version": next_version,
                "scan_status": ScanStatus.PENDING.value,
                "base_url": website.base_url,
                "pages_discovered": 0,
                "pages_scraped": 0,
                "pages_failed": 0,
                "current_step": "Initializing snapshot",
                "started_at": datetime.utcnow(),
                "total_insights": 0,
                "critical_issues": 0,
                "warnings": 0,
                "good_practices": 0
            }
            
            result = await self.snapshots_collection.insert_one(snapshot_doc)
            snapshot_doc["_id"] = result.inserted_id
            
            # Update website's snapshot count
            await self.website_controller.update_snapshot_count(request.website_id)
            
            logger.info(f"Created snapshot v{next_version} for website {request.website_id}")
            
            # Start the background scan
            asyncio.create_task(self._run_snapshot_scan(str(result.inserted_id)))
            
            return WebsiteSnapshot(**snapshot_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create snapshot"
            )
    
    async def get_website_snapshots(self, user_id: str, website_id: str, limit: int = 10) -> List[WebsiteSnapshot]:
        """Get snapshots for a website"""
        try:
            # Verify user owns the website
            await self.website_controller.get_website(user_id, website_id)
            
            cursor = self.snapshots_collection.find({
                "website_id": PyObjectId(website_id),
                "user_id": user_id
            }).sort("version", -1).limit(limit)
            
            snapshots = await cursor.to_list(length=None)
            return [WebsiteSnapshot(**snapshot) for snapshot in snapshots]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting snapshots: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve snapshots"
            )
    
    async def get_snapshot(self, user_id: str, snapshot_id: str) -> WebsiteSnapshot:
        """Get a specific snapshot"""
        try:
            snapshot = await self.snapshots_collection.find_one({
                "_id": PyObjectId(snapshot_id),
                "user_id": user_id
            })
            
            if not snapshot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Snapshot not found"
                )
                
            return WebsiteSnapshot(**snapshot)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting snapshot: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve snapshot"
            )
    
    async def get_snapshot_pages(self, user_id: str, snapshot_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pages for a snapshot"""
        try:
            # Verify user owns the snapshot
            await self.get_snapshot(user_id, snapshot_id)
            
            cursor = self.pages_collection.find({
                "snapshot_id": PyObjectId(snapshot_id),
                "user_id": user_id
            }).limit(limit)
            
            return await cursor.to_list(length=None)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting snapshot pages: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve snapshot pages"
            )
    
    async def _run_snapshot_scan(self, snapshot_id: str):
        """Background task to run the snapshot scan"""
        try:
            from ...scrape.runScrape import complete_scan
            
            # Get snapshot details
            snapshot = await self.snapshots_collection.find_one({"_id": PyObjectId(snapshot_id)})
            if not snapshot:
                logger.error(f"Snapshot {snapshot_id} not found for scanning")
                return
            
            # Update status to crawling
            await self._update_snapshot_status(snapshot_id, {
                "scan_status": ScanStatus.CRAWLING.value,
                "current_step": "Discovering pages"
            })
            
            # Run the scan (reuse existing crawling logic)
            scan_result = await complete_scan(snapshot_id, snapshot["base_url"])
            
            if scan_result and scan_result.get("success"):
                # Process the scraped data into our new structure
                await self._process_snapshot_data(snapshot_id)
                
                # Update final status
                await self._update_snapshot_status(snapshot_id, {
                    "scan_status": ScanStatus.COMPLETED.value,
                    "current_step": "Scan completed",
                    "completed_at": datetime.utcnow()
                })
            else:
                await self._update_snapshot_status(snapshot_id, {
                    "scan_status": ScanStatus.FAILED.value,
                    "current_step": "Scan failed",
                    "error_message": scan_result.get("error", "Unknown error"),
                    "completed_at": datetime.utcnow()
                })
                
        except Exception as e:
            logger.error(f"Snapshot scan failed: {str(e)}")
            await self._update_snapshot_status(snapshot_id, {
                "scan_status": ScanStatus.FAILED.value,
                "current_step": "Error occurred",
                "error_message": str(e),
                "completed_at": datetime.utcnow()
            })
    
    async def _update_snapshot_status(self, snapshot_id: str, updates: Dict[str, Any]):
        """Update snapshot status"""
        try:
            await self.snapshots_collection.update_one(
                {"_id": PyObjectId(snapshot_id)},
                {"$set": updates}
            )
        except Exception as e:
            logger.error(f"Failed to update snapshot status: {e}")
    
    async def _process_snapshot_data(self, snapshot_id: str):
        """Process scraped data from webpages collection into page_snapshots"""
        try:
            # Get all webpage data for this snapshot (from old system)
            webpages_cursor = db.webpages.find({"analysis_id": snapshot_id})
            webpages = await webpages_cursor.to_list(length=None)
            
            snapshot = await self.snapshots_collection.find_one({"_id": PyObjectId(snapshot_id)})
            if not snapshot:
                return
            
            total_insights = 0
            critical_issues = 0
            warnings = 0
            good_practices = 0
            
            for webpage in webpages:
                # Extract data from the old format
                url = webpage.get("url", "")
                parsed_url = urlparse(url)
                
                # Extract SEO data
                title = webpage.get("title", "")
                meta = webpage.get("meta", {})
                meta_description = meta.get("SEO", {}).get("description", "")
                headings = webpage.get("headings", {})
                
                # Calculate content hash for change detection
                content = webpage.get("content", "")
                content_hash = hashlib.md5(content.encode()).hexdigest() if content else None
                
                # Count insights
                insights = webpage.get("insights", {})
                page_critical = len(insights.get("Immediate Action Required", []))
                page_warnings = len(insights.get("Needs Attention", []))
                page_good = len(insights.get("Good Practice", []))
                
                total_insights += page_critical + page_warnings + page_good
                critical_issues += page_critical
                warnings += page_warnings
                good_practices += page_good
                
                # Create page snapshot document
                page_doc = {
                    "website_id": snapshot["website_id"],
                    "snapshot_id": PyObjectId(snapshot_id),
                    "user_id": snapshot["user_id"],
                    "url": url,
                    "url_path": parsed_url.path,
                    "title": title,
                    "meta_description": meta_description,
                    "h1_tags": headings.get("h1", []),
                    "h2_tags": headings.get("h2", []),
                    "word_count": len(content.split()) if content else 0,
                    "seo_data": webpage,  # Store full scraped data
                    "insights": insights,
                    "content_hash": content_hash,
                    "scraped_at": datetime.utcnow()
                }
                
                # Insert page snapshot
                await self.pages_collection.insert_one(page_doc)
            
            # Update snapshot summary stats
            await self.snapshots_collection.update_one(
                {"_id": PyObjectId(snapshot_id)},
                {"$set": {
                    "pages_scraped": len(webpages),
                    "total_insights": total_insights,
                    "critical_issues": critical_issues,
                    "warnings": warnings,
                    "good_practices": good_practices
                }}
            )
            
            logger.info(f"Processed {len(webpages)} pages for snapshot {snapshot_id}")
            
        except Exception as e:
            logger.error(f"Error processing snapshot data: {str(e)}") 