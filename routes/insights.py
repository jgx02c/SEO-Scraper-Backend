from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import logging
from db import settings_collection  # Import your MongoDB collection from db.py
from rag_input import get_insight_for_input  # Assuming this function generates the insight
from default_prompts import DEFAULT_SYSTEM_PROMPT  # Assuming this is your system prompt
from bson import ObjectId  # Import ObjectId to handle MongoDB ObjectId serialization

logger = logging.getLogger(__name__)

insights_bp = Blueprint("insights", __name__)

# Function to handle ObjectId serialization
def serialize_objectid(data):
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: serialize_objectid(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_objectid(item) for item in data]
    return data

@insights_bp.route('/generate_insight', methods=['POST'])
def handle_generate_insight():
    try:
        # Hardcoded settings ID (ensure this is unique or predefined)
        SETTINGS_ID = ObjectId("67aaf294a5502d73f197c464")  # Replace with a real ObjectId
        
        # Default settings (centralized)
        DEFAULT_SETTINGS = {
            "model": "gpt-4o",
            "temperature": 0.8,
            "presence_penalty": 0.6,
            "vectorStore": "leaps",
            "prompt": DEFAULT_SYSTEM_PROMPT  # Assuming this is defined elsewhere
        }

        # Get raw message data
        data = request.get_data(as_text=True)
        message = data.strip()

        if not message:
            return jsonify({
                "error": "No message provided",
                "timestamp": datetime.utcnow().isoformat()
            }), 400

        # Retrieve settings from database using hardcoded ID
        settings = settings_collection.find_one({"_id": SETTINGS_ID})

        # If settings exist, merge them with the defaults. Otherwise, use default settings.
        if settings:
            final_settings = {**DEFAULT_SETTINGS, **settings}
        else:
            final_settings = DEFAULT_SETTINGS

        # Convert any ObjectId in final_settings to string
        final_settings = serialize_objectid(final_settings)

        # Pass merged settings to get_insight_for_input
        insight_generator = get_insight_for_input(
            message,
            model=final_settings['model'],
            temperature=float(final_settings['temperature']),
            presence_penalty=float(final_settings['presence_penalty']),
            vector_store=final_settings['vectorStore'],
            system_prompt=final_settings['prompt']
        )

        insight_chunks = []

        for insight_chunk in insight_generator:
            if insight_chunk:
                insight_chunks.append(insight_chunk)

        full_insight = ''.join(insight_chunks)

        return jsonify({
            'data': full_insight,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        error_msg = f"Error in generate_insight: {e}"
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

