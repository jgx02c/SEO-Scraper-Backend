# app/routes/auth.py
from fastapi import APIRouter, Body, Depends
from ..controllers.auth_controller import AuthController
from ..models.user import UserCreate, UserLogin, PasswordResetRequest, PasswordReset
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup")
async def signup(user: UserCreate = Body(...)):
    return await AuthController.signup(user)

@router.post("/signin")
async def signin(user: UserLogin = Body(...)):
    return await AuthController.signin(user)

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest = Body(...)):
    return await AuthController.forgot_password(request)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset = Body(...)):
    return await AuthController.reset_password(reset_data)

@router.get("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    return await AuthController.validate_token(current_user)