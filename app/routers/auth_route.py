from fastapi import APIRouter, Request, HTTPException
from ..utils.jwt_utils import check_jwt, issue_jwt  # Import the JWT utility functions
from app.controllers.userController import create_user
from app.models.authModel import LoginRequest, SignupRequest

router = APIRouter()

# Endpoint to login and return JWT token
@router.post("/login", tags=["users"])
async def login_endpoint(request: Request, login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    # Replace this with actual authentication logic
    if login_data.username == "testuser" and login_data.password == "password":  # Dummy check
        token = issue_jwt(login_data.username)  # Issue a JWT token for the user
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Endpoint to logout (invalidate the token on the client side)
@router.post("/logout", tags=["users"])
async def logout_endpoint(request: Request):
    """Logout user and invalidate the JWT token (on the client side)"""
    await check_jwt(request.headers["Authorization"].replace("Bearer ", ""))  # Validate the token
    # For this simple example, we'll just return a message indicating successful logout
    # In a real application, you would handle token invalidation client-side (remove the token)
    return {"message": "Successfully logged out"}

@router.post("/create-user", tags=["users"])
async def create_user_endpoint(request: Request, signup_data: SignupRequest): 
    try: 
        new_user = await create_user(SignupRequest)
        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create users")
    except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    return {"message": "User created successfully", "users": new_user}