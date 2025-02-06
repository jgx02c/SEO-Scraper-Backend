from ..db.mongoConnect import get_collection 
from bson import ObjectId
from fastapi import HTTPException

collection = get_collection("services")  # Get the services collection

# Working 2-4-25
async def create_service(service_data: dict):
    print("Trying to create service") 
    service_data["_id"] = str(ObjectId())  # Generate unique ID
    result = await collection.insert_one(service_data)# stops around here
    
    if result.inserted_id:
        print("Created service!")
        return {**service_data, "_id": str(result.inserted_id)}
    
    print("Failed to create service!")
    return None 

# Working 2-4-25
async def delete_service(service_data: dict): 
    print("Trying to delete service")  
    print("Received service_data:", service_data)  # Debugging

    if "_id" not in service_data:
        print("No _id provided!")
        raise HTTPException(status_code=400, detail="Service ID is required")

    try:
        object_id = ObjectId(service_data["_id"])  # Convert to ObjectId
    except Exception:
        print("Invalid ID format!")
        raise HTTPException(status_code=400, detail="Invalid service ID format")

    result = await collection.delete_one({"_id": service_data["_id"]})  
    print("Delete result:", result) 
    
    if result.deleted_count > 0:
        print("Deleted service!")
        return {"message": "Service deleted successfully"}
    
    print("Failed to delete service!")
    raise HTTPException(status_code=404, detail="No matching service found")

# Working 2-4-25 
async def get_services(): 
    print("Trying to get services")  
    services = []
    async for service in collection.find(): 
        services.append(service)
    if services:
        print("Obtained services!")
        return services
    
    print("Failed to get services!")
    raise HTTPException(status_code=500, detail="Failed to get services")

