from ..db.mongoConnect import get_collection
from bson import ObjectId
from fastapi import HTTPException

collection = get_collection("data") # Get the data collection

# When the service is created, it calls a function in Utils to create the 
# Initial Data JSON in MongoDB. view ./utils for data creations

async def get_data(): 
    print("Trying to get data")  
    data = []
    async for item in collection.find(): 
        data.append(item)
    if data:
        print("Obtained data!")
        return data
    
    print("Failed to get data!")
    raise HTTPException(status_code=500, detail="Failed to get data")

async def edit_data(data: dict): 
    print("Trying to edit data") 
    data["_id"] = str(ObjectId())  # Generate unique ID
    result = await collection.find_one_and_update(data)# stops around here
    
    if result:
        print("Edited data!")
        return {**data, "_id": str(result)}
    
    print("Failed to edit data!")
    return None 


async def delete_data(data: dict):
    print("Trying to delete data")  
    print("Received data:", data)  # Debugging

    if "_id" not in data:
        print("No _id provided!")
        raise HTTPException(status_code=400, detail="Data ID is required")

    try:
        object_id = ObjectId(data["_id"])  # Convert to ObjectId
    except Exception:
        print("Invalid ID format!")
        raise HTTPException(status_code=400, detail="Invalid Data ID format")

    result = await collection.delete_one({"_id": data["_id"]})  
    print("Delete result:", result) 
    
    if result.deleted_count > 0:
        print("Deleted data!")
        return {"message": "Data deleted successfully"}
    
    print("Failed to delete data!")
    raise HTTPException(status_code=404, detail="No matching data found")