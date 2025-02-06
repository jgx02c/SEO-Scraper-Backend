from ..db.mongoConnect import get_collection
from fastapi import HTTPException
from bson.objectid import ObjectId

db_collection = get_collection("prompts")

async def savePrompts(updated_prompts: dict):
    try:
        # Assuming there's only one document in the collection, fetch the first one
        existing_prompts = await db_collection.find_one({})
        
        if not existing_prompts:
            raise HTTPException(status_code=404, detail="Prompts document not found")

        # Replace the existing document with the updated one
        result = await db_collection.replace_one(
            {"_id": existing_prompts["_id"]},  # Filter by the existing document's _id
            updated_prompts,  # The new document data
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update prompts")

        return {"message": "Prompts updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prompts: {str(e)}")
