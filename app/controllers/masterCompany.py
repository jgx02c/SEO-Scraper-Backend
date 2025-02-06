# controllers/masterCompany.py
from fastapi import HTTPException
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["your_database"]
company_collection = db["companies"]

# Function to add the master company
async def addMasterCompany(company_data: dict):
    try:
        # Insert the company into the database with 'is_master' flag set to True
        company_data['is_master'] = True  # Ensure it's marked as the master company
        result = await company_collection.insert_one(company_data)
        return {"message": "Master company added successfully", "company_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding master company: {str(e)}")

# Function to delete the master company
async def deleteMasterCompany():
    try:
        # Delete the master company based on 'is_master' flag
        result = await company_collection.delete_one({"is_master": True})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Master company not found")
        return {"message": "Master company deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting master company: {str(e)}")

# Function to get the master company
async def getMasterCompany():
    try:
        # Retrieve the master company based on 'is_master' flag
        company = await company_collection.find_one({"is_master": True})
        if not company:
            raise HTTPException(status_code=404, detail="Master company not found")
        # Convert ObjectId to string for JSON compatibility
        company["_id"] = str(company["_id"])
        return company
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching master company: {str(e)}")
