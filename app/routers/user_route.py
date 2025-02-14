from fastapi import APIRouter, HTTPException, Request
from ..controllers.userController import get_user, edit_user, delete_user
from app.models.userModel import User

router = APIRouter()

@router.get("/get-user", tags=["users"])
async def get_users_endpoint(request: Request):

    try: 
        found_users = await get_user()
        if not found_users:
            raise HTTPException(status_code=500, detail="Failed to get users")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "Users obtained successfully", "users": found_users}
    

@router.post("/edit-user", tags=["users"])
async def edit_user_endpoint(request: Request, user_data: User):

    try: 
        edited_user = await edit_user(user_data.dict())
        if not edited_user:
            raise HTTPException(status_code=500, detail="Failed to edit user")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User edited successfully", "users": edited_user}


@router.post("/delete-user", tags=["users"])
async def delete_user_endpoint(request: Request, user_data: User):

    try:
        json_body = await request.json()
        print("Raw request JSON:", json_body)
    except Exception as e:
        print("Failed to read request JSON:", e)
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    if not json_body:
        raise HTTPException(status_code=400, detail="Request body is empty")

    try: 
        deleted_user = await delete_user(json_body)
        if not deleted_user:
            raise HTTPException(status_code=500, detail="Failed to get services")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User Deleted Successfully!", "users": deleted_user}