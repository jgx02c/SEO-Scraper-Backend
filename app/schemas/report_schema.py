from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportBase(BaseModel):
    report_type: str
    status: str

class ReportCreate(ReportBase):
    business_id: Optional[int] = None

class ReportResponse(ReportBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    report_data: dict

    class Config:
        orm_mode = True
