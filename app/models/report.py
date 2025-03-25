from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class InsightsCount(BaseModel):
    immediate_action_required: int = Field(0, alias="Immediate Action Required")
    needs_attention: int = Field(0, alias="Needs Attention")
    good_practice: int = Field(0, alias="Good Practice")

    class Config:
        allow_population_by_field_name = True


class PageReport(BaseModel):
    website_url: str
    insights_count: InsightsCount
    error_citations: List[Any] = []

    class Config:
        allow_population_by_field_name = True


class SeoReport(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    report_date: datetime
    filename: str
    insights_count: InsightsCount
    insights_breakdown: Dict[str, Any] = {}
    total_insights: int
    page_reports: List[PageReport] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class FetchOverviewResponse(BaseModel):
    success: bool
    data: Optional[SeoReport] = None
    error: Optional[str] = None