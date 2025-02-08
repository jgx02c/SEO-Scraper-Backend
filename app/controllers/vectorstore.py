from ..db.mongoConnect import get_collection
from fastapi import HTTPException
from bson.objectid import ObjectId
from ..services.rag_upsert_mongo import generate_vectorestore

db_collection = get_collection("company")

async def rerun_vectorstore():
    try:
        generate_vectorestore()
        return {"message": "Created Embeddinfs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
