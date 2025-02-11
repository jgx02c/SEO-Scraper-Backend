from flask import Blueprint, jsonify
from datetime import datetime
from bson import ObjectId
import logging
from db import webpages_collection  # Import your MongoDB collection

logger = logging.getLogger(__name__)

pages_bp = Blueprint("pages", __name__)

@pages_bp.route('/get_pages_by_business_id/<business_id>', methods=['GET'])
def get_pages_by_business_id(business_id):
    try:
        # Convert business_id to integer
        business_id_int = int(business_id)
        
        # Define the projection to exclude the data field
        projection = {
            "data": 0  # 0 means exclude, 1 would mean include
        }
        
        # Query with the correct business_id format and projection
        query = {"business_id": business_id_int}
        
        # Get all pages without the data field
        pages = list(webpages_collection.find(query, projection))
        
        # Format the response
        formatted_pages = []
        for page_doc in pages:
            formatted_page = {
                "filename": page_doc.get("filename"),
                "admin_Business": page_doc.get("admin_Business"),
                "business_id": page_doc.get("business_id"),
                "_id": str(page_doc["_id"])  # Convert ObjectId to string
            }
            formatted_pages.append(formatted_page)
        
        return jsonify({
            "data": formatted_pages,
            "total_count": len(formatted_pages),
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid business ID",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error fetching pages for business {business_id}: {e}")
        return jsonify({
            "error": f"Error fetching pages: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@pages_bp.route('/get_page_by_id/<page_id>', methods=['GET'])
def get_page_by_id(page_id):
    try:
        # Convert string ID to MongoDB ObjectId
        object_id = ObjectId(page_id)
        
        # Query using _id instead of page_id
        page = webpages_collection.find_one({"_id": object_id})
        
        if page:
            # Convert ObjectId to string for JSON serialization
            page['_id'] = str(page['_id'])
            
            # Handle $numberInt in business_id if present
            if isinstance(page.get('business_id'), dict) and '$numberInt' in page['business_id']:
                page['business_id'] = int(page['business_id']['$numberInt'])
            
            return jsonify({
                "data": page,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        return jsonify({
            "error": "Page not found",
            "timestamp": datetime.utcnow().isoformat()
        }), 404
        
    except Exception as e:
        logger.error(f"Error fetching page {page_id}: {e}")
        return jsonify({
            "error": f"Error fetching page: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
