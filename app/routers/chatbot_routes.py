from fastapi import APIRouter, HTTPException, Depends
from chatbot.chatbot_service import get_chatbot_response
from auth.jwt_handler import get_current_user
from sqlalchemy.orm import Session
from db.database import get_db

chatbot_router = APIRouter()

@chatbot_router.post("/query")
def query_chatbot(question: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Ask the chatbot a question (e.g., SEO, competitor analysis, recommendations)."""
    response = get_chatbot_response(question, user)
    if not response:
        raise HTTPException(status_code=400, detail="Failed to get chatbot response.")
    return {"response": response}

@chatbot_router.get("/history")
def get_chatbot_history(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Retrieve the history of chatbot interactions."""
    history = get_chatbot_response(user)
    if not history:
        raise HTTPException(status_code=404, detail="No chatbot history found.")
    return history
