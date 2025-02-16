# app/routes/auth.py
from fastapi import APIRouter, Body
from ..controllers.auth_controller import AuthController
from ..models.user import UserCreate, UserLogin, PasswordResetRequest, PasswordReset

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