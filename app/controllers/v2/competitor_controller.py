"""
Competitor Controller V2

Handles competitor-specific operations and analysis.
Focused on competitor tracking and competitive analysis.
"""

from fastapi import HTTPException, status
from ...models.website import (
    Website, WebsiteCreateRequest, WebsiteType, CompetitorAnalysis
)
from .website_controller import WebsiteController
from .snapshot_controller import SnapshotController
from .comparison_controller import ComparisonController
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CompetitorController:
    """Controller for competitor operations"""
    
    def __init__(self):
        self.website_controller = WebsiteController()
        self.snapshot_controller = SnapshotController()
        self.comparison_controller = ComparisonController()
        
    async def add_competitor(self, user_id: str, request: WebsiteCreateRequest) -> Website:
        """Add a new competitor website"""
        try:
            # Force website type to competitor
            request.website_type = WebsiteType.COMPETITOR
            
            # Create the competitor website
            competitor = await self.website_controller.create_website(user_id, request)
            
            logger.info(f"Added competitor {competitor.domain} for user {user_id}")
            return competitor
            
        except Exception as e:
            logger.error(f"Error adding competitor: {str(e)}")
            raise
    
    async def get_competitors(self, user_id: str) -> List[Website]:
        """Get all competitor websites for a user"""
        try:
            return await self.website_controller.get_user_websites(
                user_id, WebsiteType.COMPETITOR
            )
        except Exception as e:
            logger.error(f"Error getting competitors: {str(e)}")
            raise
    
    async def get_primary_websites(self, user_id: str) -> List[Website]:
        """Get all primary websites for a user"""
        try:
            return await self.website_controller.get_user_websites(
                user_id, WebsiteType.PRIMARY
            )
        except Exception as e:
            logger.error(f"Error getting primary websites: {str(e)}")
            raise
    
    async def analyze_against_competitors(self, user_id: str, primary_website_id: str) -> Dict[str, Any]:
        """Analyze a primary website against all competitors"""
        try:
            # Get primary website
            primary_website = await self.website_controller.get_website(user_id, primary_website_id)
            
            # Get competitors
            competitors = await self.get_competitors(user_id)
            
            if not competitors:
                return {
                    "primary_website": primary_website,
                    "competitors": [],
                    "analysis": {
                        "message": "No competitors added yet"
                    }
                }
            
            # Get latest snapshots for primary website
            primary_snapshots = await self.snapshot_controller.get_website_snapshots(
                user_id, primary_website_id, limit=1
            )
            
            if not primary_snapshots:
                return {
                    "primary_website": primary_website,
                    "competitors": competitors,
                    "analysis": {
                        "message": "No snapshots available for primary website"
                    }
                }
            
            primary_snapshot = primary_snapshots[0]
            
            # Analyze against each competitor
            competitor_analyses = []
            
            for competitor in competitors:
                competitor_snapshots = await self.snapshot_controller.get_website_snapshots(
                    user_id, str(competitor.id), limit=1
                )
                
                if competitor_snapshots:
                    competitor_snapshot = competitor_snapshots[0]
                    analysis = await self._compare_websites(
                        primary_snapshot, competitor_snapshot, competitor
                    )
                    competitor_analyses.append(analysis)
                else:
                    competitor_analyses.append({
                        "competitor": competitor,
                        "status": "no_snapshots",
                        "message": f"No snapshots available for {competitor.name}"
                    })
            
            # Generate overall competitive analysis
            overall_analysis = self._generate_competitive_insights(
                primary_snapshot, competitor_analyses
            )
            
            return {
                "primary_website": primary_website,
                "primary_snapshot": primary_snapshot,
                "competitors": competitors,
                "competitor_analyses": competitor_analyses,
                "overall_analysis": overall_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing against competitors: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze against competitors"
            )
    
    async def _compare_websites(self, primary_snapshot, competitor_snapshot, competitor) -> Dict[str, Any]:
        """Compare primary website snapshot against competitor snapshot"""
        try:
            # Basic comparison metrics
            comparison = {
                "competitor": competitor,
                "competitor_snapshot": competitor_snapshot,
                "metrics": {
                    "pages_comparison": {
                        "primary": primary_snapshot.pages_scraped,
                        "competitor": competitor_snapshot.pages_scraped,
                        "difference": primary_snapshot.pages_scraped - competitor_snapshot.pages_scraped
                    },
                    "seo_issues_comparison": {
                        "primary_critical": primary_snapshot.critical_issues,
                        "competitor_critical": competitor_snapshot.critical_issues,
                        "primary_warnings": primary_snapshot.warnings,
                        "competitor_warnings": competitor_snapshot.warnings,
                        "primary_total": primary_snapshot.total_insights,
                        "competitor_total": competitor_snapshot.total_insights
                    }
                },
                "insights": []
            }
            
            # Generate insights based on comparison
            if primary_snapshot.critical_issues > competitor_snapshot.critical_issues:
                comparison["insights"].append({
                    "type": "threat",
                    "message": f"{competitor.name} has fewer critical SEO issues ({competitor_snapshot.critical_issues} vs {primary_snapshot.critical_issues})"
                })
            elif primary_snapshot.critical_issues < competitor_snapshot.critical_issues:
                comparison["insights"].append({
                    "type": "opportunity",
                    "message": f"You have fewer critical SEO issues than {competitor.name} ({primary_snapshot.critical_issues} vs {competitor_snapshot.critical_issues})"
                })
            
            if primary_snapshot.pages_scraped < competitor_snapshot.pages_scraped:
                comparison["insights"].append({
                    "type": "opportunity",
                    "message": f"{competitor.name} has more pages indexed ({competitor_snapshot.pages_scraped} vs {primary_snapshot.pages_scraped})"
                })
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing websites: {str(e)}")
            return {
                "competitor": competitor,
                "status": "error",
                "message": f"Failed to compare with {competitor.name}"
            }
    
    def _generate_competitive_insights(self, primary_snapshot, competitor_analyses) -> Dict[str, Any]:
        """Generate overall competitive insights"""
        try:
            successful_analyses = [
                analysis for analysis in competitor_analyses 
                if "metrics" in analysis
            ]
            
            if not successful_analyses:
                return {
                    "summary": "No competitor data available for analysis",
                    "opportunities": [],
                    "threats": []
                }
            
            # Calculate averages
            avg_competitor_pages = sum(
                analysis["metrics"]["pages_comparison"]["competitor"] 
                for analysis in successful_analyses
            ) / len(successful_analyses)
            
            avg_competitor_critical = sum(
                analysis["metrics"]["seo_issues_comparison"]["competitor_critical"] 
                for analysis in successful_analyses
            ) / len(successful_analyses)
            
            # Generate insights
            opportunities = []
            threats = []
            
            for analysis in successful_analyses:
                for insight in analysis.get("insights", []):
                    if insight["type"] == "opportunity":
                        opportunities.append(insight["message"])
                    elif insight["type"] == "threat":
                        threats.append(insight["message"])
            
            # Overall position assessment
            if primary_snapshot.pages_scraped > avg_competitor_pages:
                opportunities.append(f"You have more pages than the average competitor ({primary_snapshot.pages_scraped} vs {avg_competitor_pages:.1f})")
            else:
                threats.append(f"Competitors have more pages on average ({avg_competitor_pages:.1f} vs {primary_snapshot.pages_scraped})")
            
            if primary_snapshot.critical_issues < avg_competitor_critical:
                opportunities.append(f"You have fewer critical SEO issues than average competitor ({primary_snapshot.critical_issues} vs {avg_competitor_critical:.1f})")
            else:
                threats.append(f"You have more critical SEO issues than average competitor ({primary_snapshot.critical_issues} vs {avg_competitor_critical:.1f})")
            
            return {
                "summary": f"Analyzed against {len(successful_analyses)} competitors",
                "benchmarks": {
                    "avg_competitor_pages": avg_competitor_pages,
                    "avg_competitor_critical_issues": avg_competitor_critical,
                    "your_pages": primary_snapshot.pages_scraped,
                    "your_critical_issues": primary_snapshot.critical_issues
                },
                "opportunities": opportunities,
                "threats": threats,
                "competitive_score": self._calculate_competitive_score(
                    primary_snapshot, avg_competitor_pages, avg_competitor_critical
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating competitive insights: {str(e)}")
            return {
                "summary": "Error generating competitive analysis",
                "opportunities": [],
                "threats": []
            }
    
    def _calculate_competitive_score(self, primary_snapshot, avg_competitor_pages, avg_competitor_critical) -> Dict[str, Any]:
        """Calculate a competitive score based on key metrics"""
        try:
            # Score based on pages (more is better)
            pages_score = min(100, (primary_snapshot.pages_scraped / max(avg_competitor_pages, 1)) * 50)
            
            # Score based on critical issues (fewer is better)
            critical_score = max(0, 50 - (primary_snapshot.critical_issues / max(avg_competitor_critical, 1)) * 50)
            
            total_score = pages_score + critical_score
            
            # Determine performance level
            if total_score >= 80:
                level = "Excellent"
            elif total_score >= 60:
                level = "Good"
            elif total_score >= 40:
                level = "Average"
            else:
                level = "Needs Improvement"
            
            return {
                "total_score": round(total_score, 1),
                "pages_score": round(pages_score, 1),
                "seo_score": round(critical_score, 1),
                "performance_level": level
            }
            
        except Exception as e:
            logger.error(f"Error calculating competitive score: {str(e)}")
            return {
                "total_score": 0,
                "performance_level": "Unable to calculate"
            } 