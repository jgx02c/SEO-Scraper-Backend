"""
Website Controller V2

Handles CRUD operations for master website records.
Focused on website management without snapshot or comparison logic.
"""

from fastapi import HTTPException, status, Request
from ...database import db
from ...models.website import (
    Website, WebsiteCreateRequest, WebsiteType, PyObjectId
)
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class WebsiteController:
    """Controller for website CRUD operations"""
    
    def __init__(self):
        self.websites_collection = db.websites
        
    async def create_website(self, request: Request, create_request: WebsiteCreateRequest) -> Website:
        """Create a new master website record"""
        try:
            user_id = request.state.user["id"]
            # Extract domain from URL
            parsed_url = urlparse(str(create_request.base_url))
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
                "name": create_request.name,
                "website_type": create_request.website_type.value,
                "base_url": str(create_request.base_url),
                "crawl_frequency_days": create_request.crawl_frequency_days,
                "max_pages_per_crawl": create_request.max_pages_per_crawl,
                "tags": create_request.tags,
                "notes": create_request.notes,
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
    
    async def get_user_websites(self, request: Request, website_type: Optional[WebsiteType] = None) -> List[Website]:
        """Get all websites for a user"""
        try:
            user_id = request.state.user["id"]
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
    
    async def get_website(self, request: Request, website_id: str) -> Website:
        """Get a specific website by ID"""
        try:
            user_id = request.state.user["id"]
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
    
    async def update_website(self, request: Request, website_id: str, updates: dict) -> Website:
        """Update a website record"""
        try:
            user_id = request.state.user["id"]
            # Verify user owns the website
            await self.get_website(request, website_id)
            
            # Add updated timestamp
            updates["updated_at"] = datetime.utcnow()
            
            # Update the website
            result = await self.websites_collection.update_one(
                {"_id": PyObjectId(website_id), "user_id": user_id},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Website not found or no changes made"
                )
            
            # Return updated website
            return await self.get_website(request, website_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating website: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update website"
            )
    
    async def delete_website(self, request: Request, website_id: str) -> bool:
        """Soft delete a website (mark as inactive)"""
        try:
            user_id = request.state.user["id"]
            # Verify user owns the website
            await self.get_website(request, website_id)
            
            # Soft delete by marking as inactive
            result = await self.websites_collection.update_one(
                {"_id": PyObjectId(website_id), "user_id": user_id},
                {"$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Website not found"
                )
            
            logger.info(f"Deleted website {website_id} for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting website: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete website"
            )
    
    async def update_snapshot_count(self, website_id: str, increment: int = 1):
        """Update the total snapshots count for a website"""
        try:
            await self.websites_collection.update_one(
                {"_id": PyObjectId(website_id)},
                {
                    "$inc": {"total_snapshots": increment},
                    "$set": {
                        "last_snapshot_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating snapshot count: {str(e)}")
            # Don't raise exception as this is not critical 