import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import the blueprints
from routes.settings import settings_bp  
from routes.health import health_bp  
from routes.business import business_bp  
from routes.pages import pages_bp  
from routes.insights import insights_bp  
from routes.conversations import conversations_bp  
from routes.reports import report_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import MongoDB connection setup
from db import mongo_client, db, business_collection, webpages_collection, chat_collection, settings_collection

# Register blueprints
app = Flask(__name__)
CORS(app, 
     origins=os.getenv('CORS_ORIGINS', '*').split(','),
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# MongoDB connection with error handling
def init_mongodb():
    """Initializes MongoDB connection and returns client and db."""
    try:
        # Connect to MongoDB using the URI from environment variables
        client = MongoClient(
            os.getenv('MONGODB_URI'),
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test connection to MongoDB
        client.server_info()
        
        db = client.get_database(os.getenv('MONGODB_DB_NAME'))
        logger.info("Successfully connected to MongoDB")
        
        return client, db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise  # Reraise exception for upstream handling

# Initialize MongoDB connection when app starts
mongo_client, db = init_mongodb()

# Register blueprints
app.register_blueprint(settings_bp, url_prefix="/settings")
app.register_blueprint(health_bp, url_prefix="/health") 
app.register_blueprint(business_bp, url_prefix="/business")  
app.register_blueprint(pages_bp, url_prefix="/pages")  
app.register_blueprint(insights_bp, url_prefix="/insights")  
app.register_blueprint(conversations_bp, url_prefix="/conversations")  
app.register_blueprint(report_bp, url_prefix='/report')

# Error handler for all routes
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}", exc_info=True)
    return jsonify({
        "error": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }), 500

def create_app():
    """Factory function for creating the application instance"""
    return app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting server on port {port} with debug={debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False
    )