from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from db import settings_collection  # Correct import of your MongoDB collection from db.py
from bson import ObjectId  # For handling ObjectId explicitly

logger = logging.getLogger(__name__)

settings_bp = Blueprint("settings", __name__)

# Hardcoded _id for settings document (replace with actual ObjectId)
SETTINGS_ID = ObjectId("67aaf294a5502d73f197c464")  # Replace this with a valid ObjectId

@settings_bp.route('/get_settings', methods=['GET'])
def get_settings():
    try:
        # Get settings document by hardcoded _id
        settings = settings_collection.find_one({"_id": SETTINGS_ID})
        
        if settings:
            settings['_id'] = str(settings['_id'])  # Ensure _id is serializable to JSON
            return jsonify({
                "data": settings,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        
        # Return default settings if the document doesn't exist
        default_settings = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "presence_penalty": 0.6,
            "vectorStore": "leaps",
            "prompt": """**Instruction**:  

You are a helpful and knowledgeable SEO analysis assistant. Your goal is to provide clear, conversational explanations based on the HTML content provided. Think of yourself as a friendly expert having a natural conversation.

When responding:
- Synthesize the information naturally, as if explaining to a colleague
- Use conversational language while maintaining accuracy
- Feel free to add relevant examples or analogies when helpful
- Connect related concepts to provide better context
- Rephrase technical content in an accessible way

If the user provides a URL, do NOT attempt to fetch the page. Instead, rely only on the given context or metadata.

---
**Context**:  
{context}

**Response**:  
Please provide your response in a natural, conversational tone while ensuring all information is accurate and based on the context provided.""",
            "vectorStores": ["leaps"]
        }

        return jsonify({
            "data": default_settings,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return jsonify({
            "error": f"Error fetching settings: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@settings_bp.route('/save_settings', methods=['POST'])
def save_settings():
    try:
        settings_data = request.get_json()

        # Add timestamp to settings
        settings_data['updatedAt'] = datetime.utcnow().isoformat()

        # Ensure the document is saved with the hardcoded _id
        settings_data['_id'] = SETTINGS_ID  # Force the _id to be the same for every save
        
        # Update the existing settings document with the new data
        settings_collection.replace_one({"_id": SETTINGS_ID}, settings_data, upsert=True)
        
        return jsonify({
            "message": "Settings saved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({
            "error": f"Error saving settings: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
