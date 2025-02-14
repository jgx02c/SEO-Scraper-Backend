from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.auth.jwt_handler import create_jwt_token, verify_password, hash_password
from app.db.database import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserRegister, UserLogin, UserCreate, UserResponse
from app.auth.jwt_handler import decode_jwt_token


# Register a new user
def register_user(user: UserRegister, db: Session):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create and save the new user
    new_user = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Get the new user's id and other fields

    return new_user  # FastAPI will automatically serialize this to the UserResponse schema


# Login user and return JWT token
def login_user(user: UserLogin, db: Session):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate JWT token (the "sub" claim could be user email or user id)
    token = create_jwt_token({"sub": user.email})
    return {"access_token": token}


# Get the current user (profile)
def get_user_profile(db: Session, current_user: str):
    # Fetch the current user's profile using the email or id from the JWT token
    user = db.query(User).filter(User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user  # FastAPI will use UserResponse to serialize this model


# Edit user details (e.g., update email, name, etc.)
def edit_user(user: UserCreate, db: Session, current_user: str):
    # Fetch the current user's profile
    db_user = db.query(User).filter(User.email == current_user).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    db_user.first_name = user.first_name or db_user.first_name
    db_user.last_name = user.last_name or db_user.last_name
    db_user.password = hash_password(user.password) if user.password else db_user.password

    db.commit()
    db.refresh(db_user)
    
    return db_user  # Return the updated user


# Delete a user
def delete_user(user_id: int, db: Session):
    # Find the user by id
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user from the database
    db.delete(db_user)
    db.commit()

    return {"message": "User deleted successfully"}
