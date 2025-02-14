from ..db.mongoConnect import get_collection
from bson import ObjectId
from fastapi import HTTPException

collection = get_collection("users") ## wrong collection here too

async def get_user(user_data: dict): 
    print("Trying to get user") 

    user_id = user_data["user_id"]
    try:  
        user = await collection.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        print("Obtained user!")
        return user 
    except Exception:
        print("Failed to get user!")
        raise HTTPException(status_code=500, detail="Failed to get user")

async def create_user(user_data: dict): 
    print("Trying to create user") 
    user_data["_id"] = str(ObjectId())  # Generate unique ID
    result = await collection.insert_one(user_data)# stops around here
    
    if result.inserted_id:
        print("Created user!")
        return {**user_data, "_id": str(result.inserted_id)}
    
    print("Failed to create user!")
    return None 

async def edit_user(user_data: dict): 
    print("Trying to edit user")  
    result = await collection.find_one_and_update(user_data)# stops around here
    
    if result:
        print("Edited user!")
        return {**user_data}
    
    print("Failed to create user!")
    return None 

async def delete_user( user_data: dict): 
    print("Trying to delete user")  
    print("Received user_data:", user_data)  # Debugging

    if "user_id" not in user_data:
        print("No user_id provided!")
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        user_id = user_data["user_id"]  
    except Exception:
        print("Invalid ID format!")
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await collection.delete_one({"user_id": user_id})  
    print("Delete result:", result) 
    
    if result.deleted_count > 0:
        print("Deleted user!")
        return {"message": "User deleted successfully"}
    
    print("Failed to delete user!")
    raise HTTPException(status_code=404, detail="No matching user found")