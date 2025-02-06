from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta
from app.utils.auth import authCheck
from ..controllers.authFlowController import login
from ..controllers.authFlowController import logout
from ..controllers.userController import get_users, create_user, edit_user, delete_user

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str   
 
class CreateUserRequest (BaseModel): 
    username: str
    password: str
    company: str
    phone_num: str
    email: str
    fullname: str

class DeleteUserRequest(BaseModel):
     company: str
     _id: str
     userIP: str
     
# Endpoint to login and return JWT token
@router.post("/login", tags=["users"])
async def login(request: Request):
    await authCheck(request)
 #  if user.username == "testuser" and user.password == "password":  # Dummy check
        # Create JWT token
#      expiration = datetime.utcnow() + timedelta(hours=1)  # Set expiration time for 1 hour
   #     payload = {"sub": user.username, "exp": expiration}
 #       token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#        return {"access_token": token, "token_type": "bearer"}
  #  raise HTTPException(status_code=401, detail="Invalid credentials")
 
@router.post("/logout", tags=["users"])
async def logout(request : Request ):
# this is for testing request flow 
    await authCheck(request)


## ADMIN CALLS 
@router.get("/get-users", tags=["users"])
async def get_users_endpoint(request: Request):

    await authCheck(request); 

    try: 
        found_users = await get_users()
        if not found_users:
            raise HTTPException(status_code=500, detail="Failed to get users")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "Users obtained successfully", "users": found_users}

@router.post("/create-user", tags=["users"])
async def create_user_endpoint(request: Request, user_data: CreateUserRequest): 
    
    await authCheck(request)

    try: 
        new_user = await create_user(user_data.dict())
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create users")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User created successfully", "users": new_user}
    

@router.post("/edit-user", tags=["users"])
async def edit_user_endpoint(request: Request, user_data: CreateUserRequest):
    
    await authCheck(request)

    try: 
        edited_user = await edit_user(user_data.dict())
        if not edited_user:
            raise HTTPException(status_code=500, detail="Failed to edit user")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User edited successfully", "users": edited_user}


@router.post("/delete-user", tags=["users"])
async def delete_user_endpoint(request: Request, user_data: DeleteUserRequest):

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
        deleted_user = await delete_user(json_body)
        if not deleted_user:
            raise HTTPException(status_code=500, detail="Failed to get services")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User Deleted Successfully!", "users": deleted_user}