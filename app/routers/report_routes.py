from fastapi import APIRouter, HTTPException, Depends
from reports.report_service import create_report, get_report, delete_report
from auth.jwt_handler import get_current_user
from schemas.reportSchema import ReportCreate, ReportResponse
from sqlalchemy.orm import Session
from db.database import get_db

report_router = APIRouter()

@report_router.post("/create")
def create_new_report(report: ReportCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Creates a new SEO or competitor report."""
    report_data = create_report(report, user)
    if not report_data:
        raise HTTPException(status_code=400, detail="Error generating report.")
    return {"message": "Report creation triggered successfully", "data": report_data}

@report_router.get("/{report_id}", response_model=ReportResponse)
def get_report_by_id(report_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Retrieve a specific report by ID."""
    report = get_report(report_id, user)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@report_router.delete("/{report_id}")
def delete_report_by_id(report_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    """Delete a specific report."""
    result = delete_report(report_id, user)
    if not result:
        raise HTTPException(status_code=400, detail="Unable to delete report.")
    return {"message": "Report deleted successfully"}
