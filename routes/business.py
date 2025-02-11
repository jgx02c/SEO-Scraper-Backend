from flask import Blueprint, jsonify
from datetime import datetime
import logging
from db import business_collection  # Import your MongoDB collection

logger = logging.getLogger(__name__)

business_bp = Blueprint("business", __name__)

@business_bp.route('/get_business_by_id/<business_id>', methods=['GET'])
def get_business_by_id(business_id):
    try:
        # Query using string business_id
        business = business_collection.find_one({"business_id": str(business_id)})

        if business:
            # Convert ObjectId to string for JSON serialization
            business['_id'] = str(business['_id'])

            # Handle any $numberInt values in the document
            for review in business.get('customer_reviews', []):
                if isinstance(review.get('age'), dict) and '$numberInt' in review['age']:
                    review['age'] = int(review['age']['$numberInt'])

            return jsonify({
                "data": business,
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        return jsonify({
            "error": "Business not found",
            "timestamp": datetime.utcnow().isoformat()
        }), 404

    except Exception as e:
        logger.error(f"Error fetching business {business_id}: {e}")
        return jsonify({
            "error": f"Error fetching business: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@business_bp.route('/get_all_businesses', methods=['GET'])
def get_all_businesses():
    try:
        businesses = list(business_collection.find())
        
        # Format each business document
        formatted_businesses = []
        for business in businesses:
            # Convert ObjectId to string
            business['_id'] = str(business['_id'])
            
            # Handle any $numberInt values in the document
            for review in business.get('customer_reviews', []):
                if isinstance(review.get('age'), dict) and '$numberInt' in review['age']:
                    review['age'] = int(review['age']['$numberInt'])
            
            formatted_businesses.append(business)
        
        if formatted_businesses:
            return jsonify({
                "data": formatted_businesses,
                "total_count": len(formatted_businesses),
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        return jsonify({
            "data": [],
            "total_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }), 200  # Return 200 with empty array instead of 404
        
    except Exception as e:
        logger.error(f"Error fetching all businesses: {e}")
        return jsonify({
            "error": f"Error fetching businesses: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
