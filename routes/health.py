from flask import Blueprint, jsonify
from datetime import datetime
import logging
from db import mongo_client  # Import your MongoDB client

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    try:
        # Check MongoDB connection
        mongo_client.server_info()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
