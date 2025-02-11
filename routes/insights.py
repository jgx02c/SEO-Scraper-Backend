from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import logging
from db import settings_collection  # Import your MongoDB collection from db.py
from rag_input import get_insight_for_input  # Assuming this function generates the insight
from default_prompts import DEFAULT_SYSTEM_PROMPT  # Assuming this is your system prompt

logger = logging.getLogger(__name__)

insights_bp = Blueprint("insights", __name__)

@insights_bp.route('/generate_insight', methods=['POST'])
def handle_generate_insight():
    try:
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

        print(f"[INFO] Received message: {message[:100]}...")  # Truncate long messages

        if not message:
            print("[ERROR] No message provided")
            return jsonify({
                "error": "No message provided",
                "timestamp": datetime.utcnow().isoformat()
            }), 400

        # Attempt to retrieve settings from database
        print("[INFO] Retrieving settings from database...")
        settings = settings_collection.find_one(
            {},  # Empty query to get any document
            sort=[('_id', -1)]  # Get the most recent document
        )
        
        # Merge default settings with retrieved settings
        if settings:
            print("[INFO] Settings found in database. Merging with defaults...")
            final_settings = {**DEFAULT_SETTINGS, **settings}
        else:
            print("[INFO] No settings found. Using default settings.")
            final_settings = DEFAULT_SETTINGS

        print("[INFO] Final settings:")
        print(json.dumps(final_settings, indent=2))

        # Pass merged settings to get_insight_for_input
        insight_generator = get_insight_for_input(
            message,
            model=final_settings['model'],
            temperature=float(final_settings['temperature']),
            presence_penalty=float(final_settings['presence_penalty']),
            vector_store=final_settings['vectorStore'],  # Caller will handle vector store initialization
            system_prompt=final_settings['prompt']
        )
        
        insight_chunks = []
        
        # Process generator in chunks
        print("[INFO] Processing insight generation...")
        for insight_chunk in insight_generator:
            if insight_chunk:
                insight_chunks.append(insight_chunk)
        
        full_insight = ''.join(insight_chunks)
        print("[INFO] Insight generation completed successfully")

        return jsonify({
            'data': full_insight,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        error_msg = f"Error in generate_insight: {e}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg)
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
