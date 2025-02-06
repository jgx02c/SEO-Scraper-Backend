from pydantic import BaseModel, HttpUrl
from typing import List, Optional

# Model for platforms
class Platform(BaseModel):
    platform_name: str
    url: HttpUrl

# Model for SEO data
class SEOData(BaseModel):
    page_url: HttpUrl
    title: str
    meta_description: str
    keywords: List[str]

# MongoDB model for the company
class Company(BaseModel):
    company_id: str
    company_name: str
    website_url: HttpUrl
    industry: str
    platforms: List[Platform]
    seo_data: List[SEOData]

    class Config:
        # Pydantic configuration for MongoDB usage
        orm_mode = True
