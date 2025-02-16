
# app/routes/user.py
from fastapi import APIRouter, Depends
from ..controllers.user_controller import UserController
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/state")
async def get_user_state(current_user: dict = Depends(get_current_user)):
    return await UserController.get_user_state(current_user)