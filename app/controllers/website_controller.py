from fastapi import HTTPException, status
from ..database import db, supabase
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
from app.scrape.generate_report import generate_report
from app.scrape.runScrape import complete_scan
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebsiteController:
    def __init__(self):
        self.analysis_collection = db.analysis
        self.reports_collection = db.reports

    async def run_analysis_tasks(self, analysis_id: str, url: str, user_email: str):
        """Background task to run the analysis"""
        try:
            logger.info(f"Starting analysis for analysis_id: {analysis_id}")
            
            # Update status to show we're starting the scan
            await self.analysis_collection.update_one(
                {"_id": analysis_id},
                {"$set": {
                    "scan_status": "scanning",
                    "current_step": "Starting website scan",
                    "last_updated": datetime.utcnow()
                }}
            )
            
            # Run the scan with proper await
            try:
                scan_result = await complete_scan(analysis_id, url)
                if not scan_result or not scan_result.get("success"):
                    raise Exception("Scan failed to complete successfully")
            except Exception as scan_error:
                logger.error(f"Scan error: {str(scan_error)}")
                raise Exception(f"Scan error: {str(scan_error)}")
            
            # Update status to show we're generating the report
            await self.analysis_collection.update_one(
                {"_id": analysis_id},
                {"$set": {
                    "scan_status": "generating_report",
                    "current_step": "Generating analysis report",
                    "last_updated": datetime.utcnow()
                }}
            )
            
            # Generate report (keep in MongoDB)
            report_result = await generate_report(analysis_id)
            if not report_result or not report_result.get("success"):
                raise Exception("Report generation failed")
            
            # Update final status
            await self.analysis_collection.update_one(
                {"_id": analysis_id},
                {"$set": {
                    "scan_status": "completed",
                    "current_step": "Analysis complete",
                    "report_generated": True,
                    "last_updated": datetime.utcnow()
                }}
            )
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Analysis failed for analysis_id {analysis_id}: {error_message}")
            
            # Update error status with detailed message
            await self.analysis_collection.update_one(
                {"_id": analysis_id},
                {"$set": {
                    "scan_status": "error",
                    "current_step": "Error occurred",
                    "error_message": error_message,
                    "last_updated": datetime.utcnow()
                }}
            )

    async def start_analysis(self, user: dict, url: str) -> dict:
        # Validate URL
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL provided"
            )

        try:
            # Generate analysis ID
            analysis_id = str(uuid4())

            # Check if profile exists
            profile_check = supabase.table("user_profiles").select("*").eq("id", user["id"]).execute()
            
            if not profile_check.data:
                # No profile exists - return error
                logger.error(f"No profile found for user {user['id']}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found. Please contact support."
                )
            
            # Update existing profile with website URL and analysis status
            profile_response = supabase.table("user_profiles").update({
                "website_url": url,
                "analysis_status": "processing",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user["id"]).execute()

            if not profile_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user profile"
                )

            # Create analysis document in MongoDB
            analysis_doc = {
                "_id": analysis_id,
                "user_id": user["id"],
                "url": url,
                "report_generated": False,
                "scan_status": "initializing",
                "pages_scanned": 0,
                "total_pages": 0,
                "current_step": "preparing",
                "estimated_time_remaining": 300,
                "created_at": datetime.utcnow(),
                "last_updated": datetime.utcnow()
            }

            # Insert into analysis collection
            await self.analysis_collection.insert_one(analysis_doc)

            # Create and track the background task
            background_task = asyncio.create_task(
                self.run_analysis_tasks(
                    analysis_id=analysis_id,
                    url=url,
                    user_email=user["email"]
                )
            )

            # Return success with analysis_id for background task
            return {
                "success": True,
                "message": "Analysis initiated",
                "url": url,
                "analysis_id": analysis_id,
                "status": "processing",
                "profile": profile_response.data[0]
            }

        except Exception as e:
            logger.error(f"Failed to start analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize analysis: {str(e)}"
            )

    async def get_analysis_status(self, user: dict) -> dict:
        try:
            # Get the latest analysis for the user
            analysis = await self.analysis_collection.find_one(
                {"user_id": user["id"]},
                sort=[("created_at", -1)]
            )

            if not analysis:
                return {
                    "success": True,
                    "status": "not_started",
                }

            return {
                "success": True,
                "status": analysis["scan_status"],
                "current_step": analysis["current_step"],
                "pages_scanned": analysis["pages_scanned"],
                "total_pages": analysis["total_pages"],
                "report_generated": analysis["report_generated"]
            }

        except Exception as e:
            logger.error(f"Error getting analysis status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving analysis status"
            )

    async def get_analysis_report(self, analysis_id: str, user: dict) -> dict:
        try:
            # Get the analysis document
            analysis = await self.analysis_collection.find_one({"_id": analysis_id})
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis not found"
                )

            # Verify user owns this analysis
            if analysis["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this analysis"
                )

            # Get the report
            report = await self.reports_collection.find_one({"analysis_id": analysis_id})
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found"
                )

            return {
                "success": True,
                "analysis": analysis,
                "report": report
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis report: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving analysis report"
            )