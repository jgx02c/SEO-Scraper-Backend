from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from files.file_service import upload_file, get_file, delete_file
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

file_router = APIRouter()

@file_router.post("/upload")
async def upload_new_file(file: UploadFile = File(...), db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Uploads a new file (e.g., scraped data, reports)."""
    file_data = await upload_file(file, user)
    if not file_data:
        raise HTTPException(status_code=400, detail="File upload failed.")
    return {"message": "File uploaded successfully", "data": file_data}

@file_router.get("/{file_id}")
def get_file_by_id(file_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Retrieve a specific file by ID."""
    file_data = get_file(file_id, user)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    return file_data

@file_router.delete("/{file_id}")
def delete_file_by_id(file_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Delete a specific file."""
    result = delete_file(file_id, user)
    if not result:
        raise HTTPException(status_code=400, detail="Unable to delete file.")
    return {"message": "File deleted successfully"}
