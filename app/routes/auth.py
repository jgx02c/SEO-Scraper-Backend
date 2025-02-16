# app/routes/auth.py
from fastapi import APIRouter, Body
from ..controllers.auth_controller import AuthController
from ..models.user import UserCreate, UserLogin, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
async def signup(user: UserCreate = Body(...)):
    return await AuthController.signup(user)

@router.post("/signin", response_model=Token)
async def signin(user: UserLogin = Body(...)):
    return await AuthController.signin(user)