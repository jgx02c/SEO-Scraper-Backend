from fastapi import APIRouter, HTTPException, Request
from app.controllers.user_controller import get_user_profile, edit_user, delete_user
from app.schemas.user_schema import UserCreate, UserResponse  # Use Pydantic schemas
from app.db.database import get_db
from app.auth.jwt_handler import get_current_user  # Assuming you have a method to get current user from JWT

router = APIRouter()

# Endpoint to get the current user profile
@router.get("/get-user", tags=["users"], response_model=UserResponse)
async def get_users_endpoint(request: Request, current_user: str = Depends(get_current_user)):
    try:
        # Get user profile using the current_user (extracted from JWT)
        found_user = await get_user_profile(current_user)
        if not found_user:
            raise HTTPException(status_code=500, detail="Failed to get user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User obtained successfully", "user": found_user}

# Endpoint to edit user profile
@router.post("/edit-user", tags=["users"], response_model=UserResponse)
async def edit_user_endpoint(request: Request, user_data: UserCreate, current_user: str = Depends(get_current_user)):
    try:
        # Edit user profile
        edited_user = await edit_user(user_data, current_user)
        if not edited_user:
            raise HTTPException(status_code=500, detail="Failed to edit user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User edited successfully", "user": edited_user}

# Endpoint to delete a user
@router.post("/delete-user", tags=["users"])
async def delete_user_endpoint(request: Request, user_data: UserCreate, current_user: str = Depends(get_current_user)):
    try:
        # Call delete_user controller method (passing data from the request)
        deleted_user = await delete_user(user_data.dict())  # assuming dict() converts Pydantic model to dict
        if not deleted_user:
            raise HTTPException(status_code=500, detail="Failed to delete user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "User deleted successfully!", "user": deleted_user}
