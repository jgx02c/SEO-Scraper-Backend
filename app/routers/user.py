# routes.py
from fastapi import APIRouter
from fastapi import WebSocket, HTTPException
from ..controllers.chatData import chatData
from ..controllers.addCompany import addCompany
from ..controllers.getCompanies import getCompanies
from ..controllers.getCompany import getCompany
from ..controllers.deleteCompany import deleteCompany
from ..controllers.scraper import rerun_company_scraper
from ..controllers.vectorstore import rerun_vectorstore

router = APIRouter()

# Define the endpoint for chat data
@router.post("/chat-data", tags=["chat"])
async def chat_data_endpoint(chat_message: str, websocket: WebSocket):
    result = await chatData(chat_message, websocket)
    return result

# Trigger re-run of company scraper
@router.post("/rerun-scraper", tags=["scraper"])
async def rerun_scraper_endpoint():
    result = await rerun_company_scraper()
    return result

@router.post("/vectorstore", tags=["scraper"])
async def rerun_scraper_endpoint():
    result = await rerun_vectorstore()
    return result

@router.get("/get-companies", tags=["company"])
async def get_companies_endpoint():
    return await getCompanies()

@router.get("/get-company/{company_id}", tags=["company"])
async def get_company_endpoint(company_id: str):
    return await getCompany(company_id)
