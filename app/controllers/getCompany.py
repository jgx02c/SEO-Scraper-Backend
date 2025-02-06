from ..db.mongoConnect import get_collection
from bson import ObjectId
from fastapi import HTTPException

collection = get_collection("json") ##also probably wrong collection? 


async def get_json(): 
    print("Trying to get json data")  
    json_data = []
    async for json in collection.find(): 
        json_data.append(json)
    if json_data:
        print("Obtained jsons!")
        return json_data
    
    print("Failed to get jsons!")
    raise HTTPException(status_code=500, detail="Failed to get jsons")

async def edit_json(data: dict): 
    print("Trying to edit json") 
    data["_id"] = str(ObjectId())  # Generate unique ID
    result = await collection.insert_one(data)# stops around here
    
    if result.inserted_id:
        print("Edited json!")
        return {**data, "_id": str(result.inserted_id)}
    
    print("Failed to edit json!")
    return None 

async def delete_json(data: dict): 
    print("Trying to delete json")  
    print("Received json data:", data)  # Debugging

    if "_id" not in data:
        print("No _id provided!")
        raise HTTPException(status_code=400, detail="Json ID is required")

    try:
        object_id = ObjectId(data["_id"])  # Convert to ObjectId
    except Exception:
        print("Invalid ID format!")
        raise HTTPException(status_code=400, detail="Invalid json ID format")

    result = await collection.delete_one({"_id": data["_id"]})  
    print("Delete result:", result) 
    
    if result.deleted_count > 0:
        print("Deleted json!")
        return {"message": "JSON deleted successfully"}
    
    print("Failed to delete json!")
    raise HTTPException(status_code=404, detail="No matching json found")
