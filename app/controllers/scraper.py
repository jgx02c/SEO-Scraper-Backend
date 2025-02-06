from ..db.mongoConnect import get_collection
from fastapi import HTTPException
from bson.objectid import ObjectId

db_collection = get_collection("company")

async def rerun_company_scraper():
    try:
        delete_result = await db_collection.delete_one({"_id": ObjectId(company_id)})
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        return {"message": "Company deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
