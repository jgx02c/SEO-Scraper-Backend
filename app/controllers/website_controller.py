from fastapi import HTTPException, status
from ..dependencies import db
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
from app.scrape.generate_report import generate_report
from app.scrape.runScrape import complete_scan
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebsiteController:
    @staticmethod
    async def run_analysis_tasks(business_id: str, url: str, user_email: str):
        """Background task to run the analysis"""
        try:
            logger.info(f"Starting analysis for business_id: {business_id}")
            
            # Update status to show we're starting the scan
            await db.business.update_one(
                {"business_id": business_id},
                {
                    "$set": {
                        "scan_status": "scanning",
                        "current_step": "Starting website scan",
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Run the scan with proper await
            try:
                scan_result = await complete_scan(business_id, url)
                if not scan_result or not scan_result.get("success"):
                    raise Exception("Scan failed to complete successfully")
            except Exception as scan_error:
                logger.error(f"Scan error: {str(scan_error)}")
                raise Exception(f"Scan error: {str(scan_error)}")
            
            # Update status to show we're generating the report
            await db.business.update_one(
                {"business_id": business_id},
                {
                    "$set": {
                        "scan_status": "generating_report",
                        "current_step": "Generating analysis report",
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Generate the report with proper await
            try:
                report_result = await generate_report(business_id)
                if not report_result or not report_result.get("success"):
                    raise Exception("Report generation failed")
            except Exception as report_error:
                logger.error(f"Report error: {str(report_error)}")
                raise Exception(f"Report error: {str(report_error)}")
            
            # Update final success status
            await db.business.update_one(
                {"business_id": business_id},
                {
                    "$set": {
                        "scan_status": "completed",
                        "current_step": "Analysis complete",
                        "report_generated": True,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Update user status
            await db.users.update_one(
                {"email": user_email},
                {
                    "$set": {
                        "analysis_status": "complete",
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Analysis completed successfully for business_id: {business_id}")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Analysis failed for business_id {business_id}: {error_message}")
            
            # Update error status with detailed message
            await db.business.update_one(
                {"business_id": business_id},
                {
                    "$set": {
                        "scan_status": "error",
                        "current_step": "Error occurred",
                        "error_message": error_message,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            await db.users.update_one(
                {"email": user_email},
                {
                    "$set": {
                        "analysis_status": "error",
                        "last_updated": datetime.utcnow()
                    }
                }
            )

    @staticmethod
    async def start_analysis(user: dict, url: str) -> dict:
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
            # Generate business ID
            business_id = str(uuid4())

            # Create business document
            business_doc = {
                "business_id": business_id,
                "user_id": user["_id"],
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

            # Insert into Business collection
            await db.business.insert_one(business_doc)

            # Update user document
            await db.users.update_one(
                {"email": user["email"]},
                {
                    "$set": {
                        "website_url": url,
                        "analysis_started": datetime.utcnow(),
                        "analysis_status": "processing",
                        "last_updated": datetime.utcnow(),
                        "current_business_id": business_id
                    }
                }
            )

            # Return success with business_id for background task
            return {
                "success": True,
                "message": "Analysis initiated",
                "url": url,
                "business_id": business_id,
                "status": "processing"
            }

        except Exception as e:
            logger.error(f"Failed to start analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize analysis: {str(e)}"
            )

    @staticmethod
    async def get_analysis_status(user: dict) -> dict:
        try:
            current_user = await db.users.find_one({"email": user["email"]})
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            business_id = current_user.get("current_business_id")
            if not business_id:
                return {
                    "success": True,
                    "status": "not_started",
                }

            business_info = await db.business.find_one({"business_id": business_id})
            if not business_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business information not found"
                )

            return {
                "success": True,
                "status": current_user.get("analysis_status", "not_started"),
                "scan_status": business_info.get("scan_status", "waiting"),
                "pages_scanned": business_info.get("pages_scanned", 0),
                "total_pages": business_info.get("total_pages", 0),
                "current_step": business_info.get("current_step", "preparing"),
                "estimated_time_remaining": business_info.get("estimated_time_remaining", 300),
                "website_url": current_user.get("website_url"),
                "last_updated": business_info.get("last_updated"),
                "business_id": business_id,
                "report_generated": business_info.get("report_generated", False),
                "isComplete": current_user.get("analysis_status") == "complete"
            }

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analysis status: {str(e)}"
            )