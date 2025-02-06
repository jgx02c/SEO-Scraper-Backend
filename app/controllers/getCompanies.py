from ..db.mongoConnect import get_collection
from fastapi import HTTPException

db_collection = get_collection("company")

async def getCompanies():
    try:
        # Define the fields to include (1) or exclude (0)
        projection = {
            "_id": 1,  # Include ID
            "name": 1,  # Example: Include name
            "industry": 1,  # Example: Include industry
            "location": 1  # Example: Include location
        }
        
        companies_cursor = db_collection.find({}, projection)
        companies = await companies_cursor.to_list(length=100)  # Limit to 100 results for efficiency
        
        for company in companies:
            company["_id"] = str(company["_id"])  # Convert ObjectId to string

        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")
