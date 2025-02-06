from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.utils.auth import authCheck
from ..controllers.dataController import get_data, edit_data, delete_data

router = APIRouter()

class CreateNewDataRequest(BaseModel):
    data: str

class DeleteDataRequest(BaseModel):
    _id: str
    data: str


@router.get("/get-data", tags=["data"])
async def get_data_endpoint(request: Request):
    # Check the auth type (API Key or JWT)
    await authCheck(request) 
    try:
        data = await get_data()
        if not data:
            raise HTTPException(status_code=500, detail="Failed to obtain data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Data obtained successfully", "data": data}


@router.post("/edit-data", tags=["data"])
async def edit_data_endpoint(request: Request, data: CreateNewDataRequest ): 
    await authCheck(request)

    try:
        edited_data = await edit_data(data.dict())
        if not edited_data:
            raise HTTPException(status_code=500, detail="Failed to edit data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Data edited successfully", "data": edited_data}


@router.post("/delete-data", tags=["data"])
async def delete_data_endpoint(request: Request, data: DeleteDataRequest): 

    await authCheck(request)
    try:
        json_body = await request.json()
        print("Raw request JSON:", json_body)
    except Exception as e:
        print("Failed to read request JSON:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    if not json_body:
        raise HTTPException(status_code=400, detail="Request body is empty")

    try:
        deleted_data = await delete_data(json_body)
        if not deleted_data:
            raise HTTPException(status_code=500, detail="Failed to delete data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Data deleted successfully", "data": deleted_data}
