from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from db import chat_collection  # Import your MongoDB collection

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)

@conversations_bp.route('/get_conversations', methods=['GET'])
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
        return jsonify({
            "error": f"Error fetching conversations: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@conversations_bp.route('/save_conversation', methods=['POST'])
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
        return jsonify({
            "error": f"Error saving conversation: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500
