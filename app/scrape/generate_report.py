import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json
from collections import defaultdict
from datetime import datetime
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB configuration from .env
MONGO_URI = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME")
WEBPAGES_COLLECTION = os.getenv("MONGO_COLLECTION_WEBPAGES")
REPORTS_COLLECTION = os.getenv("MONGO_COLLECTION_REPORT")

# Initialize MongoDB connection
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def generate_report(business_id: str, filename: str = None) -> Dict[str, Any]:
    """
    Generates a detailed report for a given business_id by analyzing insights from MongoDB.
    The report is stored in the reports collection and includes an insights summary.
    
    Args:
        business_id (str): String representing the business ID to generate the report for
        filename (str, optional): Name for the report file
        
    Returns:
        Dict[str, Any]: The generated report as a dictionary with success status
    """
    try:
        logger.info(f"Starting report generation for business_id: {business_id}")
        webpages_collection = db[WEBPAGES_COLLECTION]
        reports_collection = db[REPORTS_COLLECTION]

        # Fetch all documents for the given business_id
        cursor = webpages_collection.find({"business_id": business_id})
        webpages = await cursor.to_list(length=None)
        
        if not webpages:
            logger.warning(f"No webpage data found for business_id: {business_id}")
            return {
                "success": False,
                "error": "No webpage data found for analysis"
            }

        insights_count = {"Immediate Action Required": 0, "Needs Attention": 0, "Good Practice": 0}
        insights_breakdown = defaultdict(int)
        total_insights = 0
        page_reports = []

        for webpage in webpages:
            webpage_url = webpage.get("url")  # Updated to match your data structure
            insights = webpage.get("insights", {})

            page_insights_count = {"Immediate Action Required": 0, "Needs Attention": 0, "Good Practice": 0}
            page_error_citations = []

            for section, section_insights in insights.items():
                page_insights_count[section] += len(section_insights)
                total_insights += len(section_insights)

                for insight in section_insights:
                    insights_breakdown[insight] += 1
                    page_error_citations.append({
                        "section": section,
                        "insight": insight,
                        "webpage_url": webpage_url,
                        "business_id": business_id
                    })

            page_report = {
                "website_url": webpage_url,
                "insights_count": page_insights_count,
                "error_citations": page_error_citations
            }
            page_reports.append(page_report)

            for section, count in page_insights_count.items():
                insights_count[section] += count

        # Generate the overall report
        report = {
            "business_id": business_id,
            "report_date": datetime.utcnow(),
            "filename": filename or f"report_{business_id}.pdf",
            "insights_count": insights_count,
            "insights_breakdown": dict(insights_breakdown),
            "total_insights": total_insights,
            "page_reports": page_reports
        }

        # Insert the report into MongoDB
        result = await reports_collection.insert_one(report)
        report["_id"] = str(result.inserted_id)

        logger.info(f"Report generated and stored with ID {result.inserted_id}")

        return {
            "success": True,
            "report": report,
            "report_id": str(result.inserted_id),
            "filename": report["filename"]
        }

    except Exception as e:
        error_message = f"Error generating report: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }

if __name__ == "__main__":
    import asyncio
    
    async def main():
        business_id_input = input("Enter the business_id for the report: ").strip()
        try:
            result = await generate_report(business_id_input)
            if result["success"]:
                print("Report generation complete!")
                print(f"Report ID: {result['report_id']}")
            else:
                print(f"Error: {result['error']}")
        except Exception as e:
            print(f"Error: {str(e)}")

    asyncio.run(main())