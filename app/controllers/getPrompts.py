from ..db.mongoConnect import get_collection
from fastapi import HTTPException

# Assuming your collection is called "prompts"
db_collection = get_collection("prompts")

async def getAllPrompts():
    try:
        # Retrieve all prompts from the collection
        prompts = await db_collection.find().to_list(length=None)  # None means no limit
        if not prompts:
            raise HTTPException(status_code=404, detail="No prompts found")
        # Optionally, convert the _id fields to strings
        for prompt in prompts:
            prompt["_id"] = str(prompt["_id"])
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching prompts: {str(e)}")
