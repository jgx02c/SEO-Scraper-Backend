# app/utils/mongodb.py
from bson import ObjectId
from typing import Any, Dict, List, Union
import datetime
import json
import logging

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB documents"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def serialize_mongodb_doc(doc: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Serialize MongoDB document(s) to be JSON serializable
    
    Args:
        doc: MongoDB document or list of documents
        
    Returns:
        Serialized document(s) with ObjectId converted to string, etc.
    """
    try:
        if doc is None:
            return None
            
        if isinstance(doc, list):
            return [serialize_mongodb_doc(item) for item in doc]
            
        if not isinstance(doc, dict):
            return doc
            
        result = {}
        for key, value in doc.items():
            # Convert _id to id
            if key == "_id":
                result["id"] = str(value)
                
            # Handle nested documents and lists
            elif isinstance(value, dict):
                result[key] = serialize_mongodb_doc(value)
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value if item is not None):
                result[key] = [serialize_mongodb_doc(item) for item in value]
                
            # Handle special types
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, (datetime.datetime, datetime.date)):
                result[key] = value.isoformat()
                
            # Pass through other values
            else:
                result[key] = value
                
        return result
    except Exception as e:
        logger.error(f"Error serializing MongoDB document: {e}")
        # Return original document if serialization fails
        return doc