from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from reports.report_service import generate_report_data
from db.database import get_db
from models.report_model import Report
from schemas.reportSchema import ReportCreate


# Create a new report
def create_report(report_data: ReportCreate, db: Session, user_email: str):
    # Generate report data (e.g., SEO, traffic, competitor analysis)
    generated_report = generate_report_data(report_data)

    # Create a new report entry in the database
    new_report = Report(
        user_id=user_email,  # Assume user_email can be mapped to user_id
        report_type=report_data.report_type,
        status="In Progress",  # or whatever the status is
        report_data=generated_report,
    )
    db.add(new_report)
    db.commit()

    return {"message": "Report creation initiated", "report_id": new_report.id}


# Get a specific report by ID
def get_report_by_id(report_id: int, db: Session, user_email: str):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_email).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# Delete a specific report
def delete_report(report_id: int, db: Session, user_email: str):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user_email).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"message": "Report deleted successfully"}
