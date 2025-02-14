from fastapi import HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from files.file_service import upload_file_to_backblaze
from db.database import get_db
from models.file_model import File
import os


# Upload a new file
async def upload_new_file(file: UploadFile = File(...), db: Session, user_email: str):
    # Save file to Backblaze
    file_url = await upload_file_to_backblaze(file.filename, file.file)

    # Create a file metadata entry in PostgreSQL
    new_file = File(
        user_id=user_email,
        file_name=file.filename,
        file_type=file.content_type,
        file_size=os.stat(file.filename).st_size,
        file_url=file_url,
    )
    db.add(new_file)
    db.commit()

    return {"message": "File uploaded successfully", "file_url": file_url}


# Get a specific file by ID
def get_file_by_id(file_id: int, db: Session, user_email: str):
    file = db.query(File).filter(File.id == file_id, File.user_id == user_email).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


# Delete a specific file
def delete_file(file_id: int, db: Session, user_email: str):
    file = db.query(File).filter(File.id == file_id, File.user_id == user_email).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Optionally, delete the file from Backblaze here
    # delete_file_from_backblaze(file.file_url)  # This function would be implemented separately

    db.delete(file)
    db.commit()

    return {"message": "File deleted successfully"}
