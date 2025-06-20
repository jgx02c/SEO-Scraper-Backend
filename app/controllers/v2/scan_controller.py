"""
Scan Controller V2

Handles the initiation of a website scan by combining the logic of
website creation/lookup and snapshot creation into a single flow.
This provides a simplified entry point for starting a new analysis,
similar to the deprecated V1 'start_analysis' endpoint.
"""

from fastapi import HTTPException, status, Request
from ...database import db
from ...models.website import (
    Website, WebsiteCreateRequest, WebsiteType,
    WebsiteSnapshot, SnapshotCreateRequest
)
from .website_controller import WebsiteController
from .snapshot_controller import SnapshotController
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ScanController:
    """Controller for initiating scans"""
    
    def __init__(self):
        self.websites_collection = db.websites
        self.website_controller = WebsiteController()
        self.snapshot_controller = SnapshotController()
        
    async def start_initial_scan(self, request: Request, url: str, name: str) -> WebsiteSnapshot:
        """
        Starts the first scan for a user's main website.
        It finds the main website or creates it if it doesn't exist,
        then launches a snapshot.
        """
        try:
            user_id = request.state.user["id"]
            
            # 1. Find or create the main website
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            # Check if a 'MAIN' website already exists for this user
            main_website = await self.websites_collection.find_one({
                "user_id": user_id,
                "website_type": WebsiteType.MAIN.value,
                "is_active": True
            })
            
            if main_website:
                website_id = str(main_website["_id"])
                logger.info(f"Found existing main website {website_id} for user {user_id}")
            else:
                # Create the main website if it doesn't exist
                logger.info(f"No main website found for user {user_id}. Creating one.")
                create_req = WebsiteCreateRequest(
                    name=name or domain,
                    base_url=url,
                    website_type=WebsiteType.MAIN
                )
                new_website = await self.website_controller.create_website(request, create_req)
                website_id = new_website.id
            
            # 2. Create and start a snapshot for the website
            snapshot_req = SnapshotCreateRequest(website_id=website_id)
            snapshot = await self.snapshot_controller.create_snapshot(request, snapshot_req)
            
            logger.info(f"Successfully initiated scan for website {website_id}")
            return snapshot

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating scan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate website scan."
            ) 