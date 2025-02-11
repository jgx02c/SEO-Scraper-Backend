import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from rag_input import get_insight_for_input

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Initialize Flask app first
app = Flask(__name__)
CORS(app, 
     origins=os.getenv('CORS_ORIGINS', '*').split(','),
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# Initialize SocketIO with Flask app
socketio = SocketIO(
    app,
    cors_allowed_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    transports=['websocket'],
    async_mode='eventlet'
)

# MongoDB connection with error handling
def init_mongodb():
    try:
        client = MongoClient(
            os.getenv('MONGODB_URI'),
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        # Test the connection
        client.server_info()
        db = client.get_database(os.getenv('MONGODB_DB_NAME'))
        logger.info("Successfully connected to MongoDB")
        return client, db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

try:
    mongo_client, db = init_mongodb()
    business_collection = db.business
    webpages_collection = db.webpages
    chat_collection = db.chats
    settings_collection = db.settings   
except Exception as e:
    logger.error(f"Failed to initialize MongoDB collections: {e}")
    raise

# Error handler for all routes
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}", exc_info=True)
    return jsonify({
        "error": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
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

@app.route('/get_business_by_id/<business_id>', methods=['GET'])
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
        raise

@app.route('/get_all_businesses', methods=['GET'])
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
        raise

@app.route('/get_pages_by_business_id/<business_id>', methods=['GET'])
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
        pages = list(webpages_collection.find(
            query, 
            projection
        ))
        
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
        raise

@app.route('/get_page_by_id/<page_id>', methods=['GET'])
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
        
    except InvalidId as e:
        return jsonify({
            "error": "Invalid page ID format",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Error fetching page {page_id}: {e}")
        raise

@app.route('/generate_insight', methods=['POST'])
def handle_generate_insight():
    try:
        data = request.get_data(as_text=True)
        message = data.strip()

        if not message:
            return jsonify({
                "error": "No message provided",
                "timestamp": datetime.utcnow().isoformat()
            }), 400

        # Get current settings
        settings = settings_collection.find_one(
            {},  # Empty query to get any document
            sort=[('_id', -1)]  # Get the most recent document
        )
        
        if not settings:
            # Use default settings if none exist
            settings = {
                "model": "gpt-4o",
                "temperature": 0.8,
                "presence_penalty": 0.6,
                "vectorStore": "leaps",  # This isn't actually used
                "prompt": None  # Default to None for system prompt
            }

        # Emit start event
        socketio.emit('insight_start', {
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Pass settings to get_insight_for_input
        insight_generator = get_insight_for_input(
            message,
            model=settings.get('model', 'gpt-4o'),
            temperature=float(settings.get('temperature', 0.8)),
            presence_penalty=float(settings.get('presence_penalty', 0.6)),
            vector_store="leaps",  # Hardcoded since we only use "leaps"
            system_prompt=settings.get('prompt')
        )
        
        insight_chunks = []
        
        # Process generator in chunks
        for insight_chunk in insight_generator:
            if insight_chunk:
                insight_chunks.append(insight_chunk)
                socketio.emit('insight_data', {
                    'text': insight_chunk,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        full_insight = ''.join(insight_chunks)
        socketio.emit('insight_finished', {
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return full_insight, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Error in generate_insight: {e}")
        socketio.emit('insight_error', {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })
        raise

# Chat endpoints
@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    try:
        conversations = list(chat_collection.find().sort('createdAt', -1))
        
        # Format conversations for JSON response
        formatted_conversations = []
        for conv in conversations:
            conv['_id'] = str(conv['_id'])
            formatted_conversations.append(conv)
        
        return jsonify({
            "data": formatted_conversations,
            "total_count": len(formatted_conversations),
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise

@app.route('/save_conversation', methods=['POST'])
def save_conversation():
    try:
        data = request.get_json()
        conversation_id = data.get('conversationId')
        messages = data.get('messages', [])
        
        if not conversation_id:
            return jsonify({
                "error": "No conversation ID provided",
                "timestamp": datetime.utcnow().isoformat()
            }), 400

        # Update or insert the conversation
        chat_collection.update_one(
            {"id": conversation_id},
            {
                "$set": {
                    "messages": messages,
                    "lastUpdated": datetime.utcnow().isoformat(),
                }
            },
            upsert=True
        )
        
        return jsonify({
            "message": "Conversation saved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise

# Settings endpoints
@app.route('/get_settings', methods=['GET'])
def get_settings():
    try:
        # Get the latest settings document
        settings = settings_collection.find_one(
            {},  # Empty query to get any document
            sort=[('_id', -1)]  # Get the most recent document
        )
        
        if settings:
            settings['_id'] = str(settings['_id'])
            return jsonify({
                "data": settings,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        
        # Return default settings if none exist
        default_settings = {
            "model": "gpt-4",
            "temperature": 0.7,
            "presence_penalty": 0.5,
            "vectorStore": "1",
            "prompt": "Default prompt",
            "vectorStores": ["1", "2", "3"]
        }
        
        return jsonify({
            "data": default_settings,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise

@app.route('/save_settings', methods=['POST'])
def save_settings():
    try:
        settings_data = request.get_json()
        
        # Add timestamp to settings
        settings_data['updatedAt'] = datetime.utcnow().isoformat()
        
        # Insert as a new document (keeping history)
        settings_collection.insert_one(settings_data)
        
        return jsonify({
            "message": "Settings saved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        raise

@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    
@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on_error()
def handle_socket_error(e):
    logger.error(f"SocketIO error: {e}")
    return str(e)

def create_app():
    """Factory function for creating the application instance"""
    return app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting server on port {port} with debug={debug}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False
    )