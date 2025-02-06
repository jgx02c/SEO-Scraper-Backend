# routes.py
from fastapi import APIRouter
from fastapi import WebSocket, HTTPException
from ..controllers.chatData import chatData
from ..controllers.addCompany import addCompany
from ..controllers.getCompanies import getCompanies
from ..controllers.getCompany import getCompany
from ..controllers.deleteCompany import deleteCompany
from ..controllers.getUser import getUser
from ..controllers.getPrompts import getPrompts
from ..controllers.savePrompts import savePrompts
from ..controllers.masterCompany import addMasterCompany, deleteMasterCompany, getMasterCompany
from ..controllers.purgeData import purge_all_data
from ..controllers.scraper import rerun_company_scraper

router = APIRouter()

# Define the endpoint for chat data
@router.post("/chat-data", tags=["chat"])
async def chat_data_endpoint(chat_message: str, websocket: WebSocket):
    result = await chatData(chat_message, websocket)
    return result

# Add master company endpoint
@router.post("/add-master-company", tags=["company"])
async def add_master_company_endpoint(company_data: dict):
    result = await addMasterCompany(company_data)
    return result

# Delete master company endpoint
@router.delete("/delete-master-company", tags=["company"])
async def delete_master_company_endpoint():
    result = await deleteMasterCompany()
    return result

# Get master company endpoint
@router.get("/get-master-company", tags=["company"])
async def get_master_company_endpoint():
    result = await getMasterCompany()
    return result

# Purge all data endpoint
@router.delete("/purge-all", tags=["data"])
async def purge_all_data_endpoint():
    result = await purge_all_data()
    return result

# Trigger re-run of company scraper
@router.post("/rerun-scraper", tags=["scraper"])
async def rerun_scraper_endpoint():
    result = await rerun_company_scraper()
    return result

# Other company, user, and prompt routes
@router.post("/add-company", tags=["company"])
async def add_company_endpoint(company_data: dict):
    result = await addCompany(company_data)
    return result

@router.get("/get-companies", tags=["company"])
async def get_companies_endpoint():
    return await getCompanies()

@router.get("/get-company/{company_id}", tags=["company"])
async def get_company_endpoint(company_id: str):
    return await getCompany(company_id)

@router.delete("/delete-company/{company_id}", tags=["company"])
async def delete_company_endpoint(company_id: str):
    return await deleteCompany(company_id)

@router.get("/get-user", tags=["users"])
async def get_user_endpoint():
    return await getUser()

@router.get("/get-prompts", tags=["prompts"])
async def get_prompts_endpoint():
    return await getPrompts()

@router.post("/save-prompts", tags=["prompts"])
async def save_prompts_endpoint():
    return await savePrompts()
