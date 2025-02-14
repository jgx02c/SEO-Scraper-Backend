from fastapi import APIRouter, HTTPException, Depends
from auth.jwt_handler import create_jwt_token, hash_password, verify_password
from db.database import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserRegister, UserLogin
from sqlalchemy.orm import Session

auth_router = APIRouter()

@auth_router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user."""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@auth_router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user and returns JWT token."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_jwt_token({"sub": user.email})
    return {"access_token": token}
