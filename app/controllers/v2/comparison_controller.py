"""
Comparison Controller V2

Handles snapshot comparisons and change analysis.
Focused on detecting and analyzing differences between snapshots.
"""

from fastapi import HTTPException, status, Request
from ...database import db
from ...models.website import (
    SnapshotComparison, ComparisonRequest, PyObjectId
)
from .website_controller import WebsiteController
from .snapshot_controller import SnapshotController
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ComparisonController:
    """Controller for snapshot comparison operations"""
    
    def __init__(self):
        self.comparisons_collection = db.snapshot_comparisons
        self.website_controller = WebsiteController()
        self.snapshot_controller = SnapshotController()
        
    async def compare_snapshots(self, request: Request, comparison_request: ComparisonRequest) -> SnapshotComparison:
        """Compare two snapshots to detect changes"""
        try:
            user_id = request.state.user["id"]
            # Verify user owns the website
            await self.website_controller.get_website(request, comparison_request.website_id)
            
            # Get both snapshots
            baseline = await self.snapshot_controller.get_snapshot(request, comparison_request.baseline_snapshot_id)
            current = await self.snapshot_controller.get_snapshot(request, comparison_request.current_snapshot_id)
            
            # Get pages for both snapshots
            baseline_pages = await self.snapshot_controller.get_snapshot_pages(
                request, comparison_request.baseline_snapshot_id
            )
            current_pages = await self.snapshot_controller.get_snapshot_pages(
                request, comparison_request.current_snapshot_id
            )
            
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
            seo_improvements = 0
            seo_regressions = 0
            
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
                        
                        # Count improvements/regressions
                        for category, changes in insight_change["changes"].items():
                            if category == "Immediate Action Required":
                                seo_improvements += len(changes.get("removed", []))
                                seo_regressions += len(changes.get("added", []))
                            elif category == "Needs Attention":
                                seo_improvements += len(changes.get("removed", []))
                                seo_regressions += len(changes.get("added", []))
                        
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
                "website_id": PyObjectId(comparison_request.website_id),
                "user_id": user_id,
                "baseline_snapshot_id": PyObjectId(comparison_request.baseline_snapshot_id),
                "current_snapshot_id": PyObjectId(comparison_request.current_snapshot_id),
                "pages_added": pages_added,
                "pages_removed": pages_removed,
                "pages_modified": pages_modified,
                "seo_improvements": seo_improvements,
                "seo_regressions": seo_regressions,
                "new_issues": seo_regressions,
                "resolved_issues": seo_improvements,
                "page_changes": page_changes,
                "insight_changes": insight_changes,
                "created_at": datetime.utcnow()
            }
            
            result = await self.comparisons_collection.insert_one(comparison_doc)
            comparison_doc["_id"] = result.inserted_id
            
            logger.info(f"Created comparison between snapshots {comparison_request.baseline_snapshot_id} and {comparison_request.current_snapshot_id}")
            
            return SnapshotComparison(**comparison_doc)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error comparing snapshots: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compare snapshots"
            )
    
    async def get_comparison(self, request: Request, comparison_id: str) -> SnapshotComparison:
        """Get a specific comparison by ID"""
        try:
            user_id = request.state.user["id"]
            comparison = await self.comparisons_collection.find_one({
                "_id": PyObjectId(comparison_id),
                "user_id": user_id
            })
            
            if not comparison:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comparison not found"
                )
                
            return SnapshotComparison(**comparison)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting comparison: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve comparison"
            )
    
    async def get_website_comparisons(self, request: Request, website_id: str, limit: int = 10) -> List[SnapshotComparison]:
        """Get comparisons for a website"""
        try:
            user_id = request.state.user["id"]
            # Verify user owns the website
            await self.website_controller.get_website(request, website_id)
            
            cursor = self.comparisons_collection.find({
                "website_id": PyObjectId(website_id),
                "user_id": user_id
            }).sort("created_at", -1).limit(limit)
            
            comparisons = await cursor.to_list(length=None)
            return [SnapshotComparison(**comparison) for comparison in comparisons]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting website comparisons: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve comparisons"
            )
    
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
        
        # Check H1 tag changes
        old_h1 = set(baseline.get("h1_tags", []))
        new_h1 = set(current.get("h1_tags", []))
        if old_h1 != new_h1:
            changes["h1_tags"] = {
                "added": list(new_h1 - old_h1),
                "removed": list(old_h1 - new_h1)
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
                "url": current.get("url"),
                "changes": changes
            }
        
        return None
    
    async def get_comparison_summary(self, request: Request, website_id: str) -> Dict[str, Any]:
        """Get a summary of recent comparisons for a website"""
        try:
            user_id = request.state.user["id"]
            # Verify user owns the website
            await self.website_controller.get_website(request, website_id)
            
            # Get recent comparisons
            comparisons = await self.get_website_comparisons(request, website_id, limit=5)
            
            if not comparisons:
                return {
                    "total_comparisons": 0,
                    "recent_trends": {},
                    "latest_comparison": None
                }
            
            # Calculate trends
            total_improvements = sum(c.seo_improvements for c in comparisons)
            total_regressions = sum(c.seo_regressions for c in comparisons)
            total_pages_added = sum(c.pages_added for c in comparisons)
            total_pages_removed = sum(c.pages_removed for c in comparisons)
            
            return {
                "total_comparisons": len(comparisons),
                "recent_trends": {
                    "seo_improvements": total_improvements,
                    "seo_regressions": total_regressions,
                    "pages_added": total_pages_added,
                    "pages_removed": total_pages_removed,
                    "net_seo_change": total_improvements - total_regressions
                },
                "latest_comparison": comparisons[0] if comparisons else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting comparison summary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve comparison summary"
            ) 