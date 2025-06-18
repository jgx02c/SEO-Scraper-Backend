from fastapi import HTTPException, status
from ..database import db
from ..models.website import (
    Website, WebsiteSnapshot, PageSnapshot, SnapshotComparison,
    WebsiteCreateRequest, SnapshotCreateRequest, ComparisonRequest,
    WebsiteType, ScanStatus, PyObjectId
)
from datetime import datetime, timedelta
from urllib.parse import urlparse
from uuid import uuid4
from typing import List, Dict, Any, Optional
import asyncio
import logging
import hashlib

logger = logging.getLogger(__name__)

class WebsiteV2Controller:
    """New controller for time-machine website archiving system"""
    
    def __init__(self):
        # New collections for the time-machine system
        self.websites_collection = db.websites
        self.snapshots_collection = db.website_snapshots  
        self.pages_collection = db.page_snapshots
        self.comparisons_collection = db.snapshot_comparisons
        
    # ===== WEBSITE MANAGEMENT =====
    
    async def create_website(self, user_id: str, request: WebsiteCreateRequest) -> Website:
        """Create a new master website record"""
        try:
            # Extract domain from URL
            parsed_url = urlparse(str(request.base_url))
            domain = parsed_url.netloc.replace('www.', '')
            
            # Check if website already exists for this user
            existing = await self.websites_collection.find_one({
                "user_id": user_id,
                "domain": domain,
                "is_active": True
            })
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Website {domain} already exists"
                )
            
            # Create website document
            website_doc = {
                "user_id": user_id,
                "domain": domain,
                "name": request.name,
                "website_type": request.website_type.value,
                "base_url": str(request.base_url),
                "crawl_frequency_days": request.crawl_frequency_days,
                "max_pages_per_crawl": request.max_pages_per_crawl,
                "tags": request.tags,
                "notes": request.notes,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "total_snapshots": 0,
                "last_snapshot_at": None,
                "is_active": True
            }
            
            result = await self.websites_collection.insert_one(website_doc)
            website_doc["_id"] = result.inserted_id
            
            logger.info(f"Created website record: {domain} for user {user_id}")
            return Website(**website_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating website: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create website record"
            )
    
    async def get_user_websites(self, user_id: str, website_type: Optional[WebsiteType] = None) -> List[Website]:
        """Get all websites for a user"""
        try:
            query = {"user_id": user_id, "is_active": True}
            if website_type:
                query["website_type"] = website_type.value
                
            cursor = self.websites_collection.find(query).sort("created_at", -1)
            websites = await cursor.to_list(length=None)
            
            return [Website(**website) for website in websites]
            
        except Exception as e:
            logger.error(f"Error getting websites: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve websites"
            )
    
    async def get_website(self, user_id: str, website_id: str) -> Website:
        """Get a specific website by ID"""
        try:
            website = await self.websites_collection.find_one({
                "_id": PyObjectId(website_id),
                "user_id": user_id,
                "is_active": True
            })
            
            if not website:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Website not found"
                )
                
            return Website(**website)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting website: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve website"
            )
    
    # ===== SNAPSHOT MANAGEMENT =====
    
    async def create_snapshot(self, user_id: str, request: SnapshotCreateRequest) -> WebsiteSnapshot:
        """Create a new snapshot for a website"""
        try:
            # Get the website record
            website = await self.get_website(user_id, request.website_id)
            
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
            
            # Update website's snapshot count and last snapshot time
            await self.websites_collection.update_one(
                {"_id": PyObjectId(request.website_id)},
                {
                    "$inc": {"total_snapshots": 1},
                    "$set": {
                        "last_snapshot_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
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
            await self.get_website(user_id, website_id)
            
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
    
    # ===== SCANNING LOGIC =====
    
    async def _run_snapshot_scan(self, snapshot_id: str):
        """Background task to run the snapshot scan"""
        try:
            from ..scrape.runScrape import complete_scan
            
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
    
    # ===== COMPARISON LOGIC =====
    
    async def compare_snapshots(self, user_id: str, request: ComparisonRequest) -> SnapshotComparison:
        """Compare two snapshots to detect changes"""
        try:
            # Verify user owns the website
            await self.get_website(user_id, request.website_id)
            
            # Get both snapshots
            baseline = await self.get_snapshot(user_id, request.baseline_snapshot_id)
            current = await self.get_snapshot(user_id, request.current_snapshot_id)
            
            # Get pages for both snapshots
            baseline_pages = await self._get_snapshot_pages(request.baseline_snapshot_id)
            current_pages = await self._get_snapshot_pages(request.current_snapshot_id)
            
            # Create URL maps for comparison
            baseline_urls = {page["url"]: page for page in baseline_pages}
            current_urls = {page["url"]: page for page in current_pages}
            
            # Calculate changes
            all_urls = set(baseline_urls.keys()) | set(current_urls.keys())
            pages_added = len(current_urls.keys() - baseline_urls.keys())
            pages_removed = len(baseline_urls.keys() - current_urls.keys())
            pages_modified = 0
            
            page_changes = []
            insight_changes = []
            
            for url in all_urls:
                baseline_page = baseline_urls.get(url)
                current_page = current_urls.get(url)
                
                if baseline_page and current_page:
                    # Check if page content changed
                    if baseline_page.get("content_hash") != current_page.get("content_hash"):
                        pages_modified += 1
                        page_changes.append({
                            "url": url,
                            "change_type": "modified",
                            "changes": self._detect_page_changes(baseline_page, current_page)
                        })
                    
                    # Check insight changes
                    insight_change = self._detect_insight_changes(baseline_page, current_page)
                    if insight_change:
                        insight_changes.append(insight_change)
                        
                elif current_page:
                    page_changes.append({
                        "url": url,
                        "change_type": "added"
                    })
                else:
                    page_changes.append({
                        "url": url,
                        "change_type": "removed"
                    })
            
            # Create comparison document
            comparison_doc = {
                "website_id": PyObjectId(request.website_id),
                "user_id": user_id,
                "baseline_snapshot_id": PyObjectId(request.baseline_snapshot_id),
                "current_snapshot_id": PyObjectId(request.current_snapshot_id),
                "pages_added": pages_added,
                "pages_removed": pages_removed,
                "pages_modified": pages_modified,
                "seo_improvements": 0,  # Will be calculated based on insight changes
                "seo_regressions": 0,   # Will be calculated based on insight changes
                "page_changes": page_changes,
                "insight_changes": insight_changes,
                "created_at": datetime.utcnow()
            }
            
            result = await self.comparisons_collection.insert_one(comparison_doc)
            comparison_doc["_id"] = result.inserted_id
            
            return SnapshotComparison(**comparison_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error comparing snapshots: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compare snapshots"
            )
    
    async def _get_snapshot_pages(self, snapshot_id: str) -> List[Dict[str, Any]]:
        """Get all pages for a snapshot"""
        cursor = self.pages_collection.find({"snapshot_id": PyObjectId(snapshot_id)})
        return await cursor.to_list(length=None)
    
    def _detect_page_changes(self, baseline: Dict, current: Dict) -> Dict[str, Any]:
        """Detect specific changes between two page versions"""
        changes = {}
        
        # Check title changes
        if baseline.get("title") != current.get("title"):
            changes["title"] = {
                "old": baseline.get("title"),
                "new": current.get("title")
            }
        
        # Check meta description changes
        if baseline.get("meta_description") != current.get("meta_description"):
            changes["meta_description"] = {
                "old": baseline.get("meta_description"),
                "new": current.get("meta_description")
            }
        
        # Check word count changes
        old_count = baseline.get("word_count", 0)
        new_count = current.get("word_count", 0)
        if abs(old_count - new_count) > 50:  # Significant content change
            changes["word_count"] = {
                "old": old_count,
                "new": new_count,
                "change": new_count - old_count
            }
        
        return changes
    
    def _detect_insight_changes(self, baseline: Dict, current: Dict) -> Optional[Dict[str, Any]]:
        """Detect changes in SEO insights between page versions"""
        baseline_insights = baseline.get("insights", {})
        current_insights = current.get("insights", {})
        
        changes = {}
        for category in ["Immediate Action Required", "Needs Attention", "Good Practice"]:
            old_issues = set(baseline_insights.get(category, []))
            new_issues = set(current_insights.get(category, []))
            
            added = new_issues - old_issues
            removed = old_issues - new_issues
            
            if added or removed:
                changes[category] = {
                    "added": list(added),
                    "removed": list(removed)
                }
        
        if changes:
            return {
                "url": baseline.get("url"),
                "changes": changes
            }
        
        return None 