from ..db.mongoConnect import get_collection
from fastapi import HTTPException
from bson.objectid import ObjectId

db_collection = get_collection("company")

async def getUser(company_id: str):
    try:
        company = await db_collection.find_one({"_id": ObjectId(company_id)})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company["_id"] = str(company["_id"])  # Convert ObjectId to string
        return company
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")
