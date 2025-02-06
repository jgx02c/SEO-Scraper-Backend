from ..db.mongoConnect import get_collection
from bson import ObjectId
from fastapi import HTTPException


collection = get_collection("prompts")  ## not correct collection?? 

async def get_prompts( ): 
    print("Trying to get prompts")  
    prompts = []
    async for prompt in collection.find(): 
        prompts.append(prompt)
    if prompts:
        print("Obtained prompts!")
        return prompts
    
    print("Failed to get prompts!")
    raise HTTPException(status_code=500, detail="Failed to get prompts")



async def create_prompt(prompt_data: dict): 
    print("Trying to create prompt") 
    prompt_data["_id"] = str(ObjectId())  # Generate unique ID
    result = await collection.insert_one(prompt_data)# stops around here
    
    if result.inserted_id:
        print("Created prompt!")
        return {**prompt_data, "_id": str(result.inserted_id)}
    
    print("Failed to create prompt!")
    return None 


async def delete_prompt(prompt_data: dict): 
    print("Trying to delete prompt")  
    print("Received prompt_data:", prompt_data)  # Debugging

    if "_id" not in prompt_data:
        print("No _id provided!")
        raise HTTPException(status_code=400, detail="Prompt ID is required")

    try:
        object_id = ObjectId(prompt_data["_id"])  # Convert to ObjectId
    except Exception:
        print("Invalid ID format!")
        raise HTTPException(status_code=400, detail="Invalid prompt ID format")

    result = await collection.delete_one({"_id": prompt_data["_id"]})  
    print("Delete result:", result) 
    
    if result.deleted_count > 0:
        print("Deleted prompt!")
        return {"message": "Prompt deleted successfully"}
    
    print("Failed to delete prompt!")
    raise HTTPException(status_code=404, detail="No matching prompt found")


