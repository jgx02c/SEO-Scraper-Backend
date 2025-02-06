from fastapi import APIRouter
from ..controllers.chatData import chatData
from ..controllers.addCompany import addCompany
from ..controllers.getCompanies import getCompanies
from ..controllers.getCompany import getCompany
from ..controllers.deleteCompany import deleteCompany
from ..controllers.getUser import getUser
from ..controllers.getPrompts import getPrompts
from ..controllers.savePrompts import savePrompts

router = APIRouter()

@router.get("/chat-data", tags=["chat"])
async def chat_data_endpoint():
    return await chatData()

@router.post("/add-company", tags=["company"])
async def add_company_endpoint():
    return await addCompany()

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
