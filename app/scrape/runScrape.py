import json
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from app.scrape.crawler import crawl_and_clean_urls
from app.scrape.scraper import fetch_html
from app.scrape.cleaner import process_html
import asyncio
from datetime import datetime
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB Connection using .env variables
MONGO_URI = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGODB_DB_NAME", "scopelabs")
COLLECTION_NAME = "webpages"

# Create async MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

async def update_scan_status(analysis_id: str, status: dict):
    """Update the scan status in the analysis collection"""
    try:
        await db.analysis.update_one(
            {"_id": analysis_id},
            {"$set": {
                **status,
                "last_updated": datetime.utcnow()
            }}
        )
    except Exception as e:
        logger.error(f"Failed to update scan status: {e}")

async def complete_scan(analysis_id: str, base_url: str):
    """
    Crawls a website, fetches and cleans each page, and upserts the cleaned data into MongoDB.
    Provides regular status updates during the process.
    """
    try:
        logger.info(f"Starting scan for analysis_id: {analysis_id}, url: {base_url}")
        
        # Update initial status
        await update_scan_status(analysis_id, {
            "scan_status": "crawling",
            "current_step": "Discovering pages",
            "pages_scanned": 0,
            "total_pages": 0
        })

        # Get list of URLs to process
        urls = await crawl_and_clean_urls(base_url)  # Make sure this is async too
        total_pages = len(urls)
        pages_scanned = 0

        # Update status with total pages
        await update_scan_status(analysis_id, {
            "total_pages": total_pages,
            "current_step": "Starting page analysis"
        })

        for url in urls:
            try:
                logger.info(f"Processing: {url}")
                
                # Update current page status
                await update_scan_status(analysis_id, {
                    "scan_status": "scanning",
                    "current_step": f"Analyzing page {pages_scanned + 1} of {total_pages}",
                    "pages_scanned": pages_scanned,
                    "current_url": url
                })

                # Fetch raw HTML
                html_content = await fetch_html(url)  # Make sure this is async too

                if not html_content:
                    logger.warning(f"Skipping {url} (No content found)")
                    continue

                # Clean and extract SEO data
                cleaned_data = await process_html(html_content)  # Make sure this is async too
                cleaned_data_dict = json.loads(cleaned_data)

                # Attach analysis ID and URL to the document
                cleaned_data_dict["analysis_id"] = analysis_id
                cleaned_data_dict["url"] = url

                # Upsert into MongoDB
                await collection.update_one(
                    {"url": url, "analysis_id": analysis_id},
                    {"$set": cleaned_data_dict},
                    upsert=True
                )

                pages_scanned += 1
                logger.info(f"Upserted data for {url}")

                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
                continue

        # Update completion status
        await update_scan_status(analysis_id, {
            "scan_status": "completed",
            "current_step": "Scan completed",
            "pages_scanned": pages_scanned,
            "completion_time": datetime.utcnow()
        })

        logger.info("Scan complete.")
        return {"success": True, "message": "Scan completed successfully"}

    except Exception as e:
        error_message = f"Scan failed: {str(e)}"
        logger.error(error_message)
        
        # Update error status
        await update_scan_status(analysis_id, {
            "scan_status": "error",
            "current_step": "Error occurred",
            "error_message": error_message
        })
        
        return {"success": False, "error": error_message}

if __name__ == "__main__":
    async def main():
        analysis_id = input("Enter Analysis ID: ").strip()
        base_url = input("Enter Base URL: ").strip()

        if analysis_id and base_url:
            await complete_scan(analysis_id, base_url)
        else:
            print("Analysis ID and Base URL are required!")

    asyncio.run(main())