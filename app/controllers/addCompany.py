# controllers/addCompany.py
from fastapi import HTTPException
#from ..services.add_company_service import add_company_to_db  # Assuming you have a service to add a company

# Controller function to add a company
async def addCompany(company_data: dict):
    try:
        # Here we call the service function that handles adding the company to the database
        '''company_id = await add_company_to_db(company_data)
        
        if not company_id:
            raise HTTPException(status_code=400, detail="Failed to add company")

        return {"message": "Company added successfully", "company_id": company_id}
'''
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding company: {str(e)}")
