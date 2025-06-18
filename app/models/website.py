from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from bson import ObjectId
from enum import Enum

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

class WebsiteType(str, Enum):
    """Types of websites being tracked"""
    PRIMARY = "primary"      # User's main website
    COMPETITOR = "competitor"  # Competitor website
    REFERENCE = "reference"   # Reference/inspiration website

class ScanStatus(str, Enum):
    """Status of a scan/snapshot"""
    PENDING = "pending"
    CRAWLING = "crawling"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Master Website Record
class Website(BaseModel):
    """Master record for a website - persistent across all snapshots"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # Owner of this website record
    domain: str  # Base domain (e.g., "example.com")
    name: str  # Human-readable name
    website_type: WebsiteType
    base_url: HttpUrl  # Primary URL to scrape
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracking info
    total_snapshots: int = 0
    last_snapshot_at: Optional[datetime] = None
    is_active: bool = True
    
    # Settings
    crawl_frequency_days: int = 7  # How often to auto-crawl
    max_pages_per_crawl: int = 50
    tags: List[str] = []  # User-defined tags
    notes: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

# Snapshot of a website at a point in time
class WebsiteSnapshot(BaseModel):
    """A versioned snapshot of a website at a specific point in time"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    website_id: PyObjectId  # Reference to master Website record
    user_id: str
    
    # Snapshot metadata
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    version: int  # Incremental version number for this website
    scan_status: ScanStatus = ScanStatus.PENDING
    
    # Scan details
    base_url: str
    pages_discovered: int = 0
    pages_scraped: int = 0
    pages_failed: int = 0
    scan_duration_seconds: Optional[int] = None
    
    # Status tracking
    current_step: str = "Initializing"
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Summary stats (calculated after scan)
    total_insights: int = 0
    critical_issues: int = 0
    warnings: int = 0
    good_practices: int = 0
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

# Individual page data within a snapshot
class PageSnapshot(BaseModel):
    """Individual page data within a website snapshot"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    website_id: PyObjectId
    snapshot_id: PyObjectId
    user_id: str
    
    # Page identification
    url: str
    url_path: str  # Path portion of URL for easier querying
    page_type: str = "page"  # page, post, product, etc.
    
    # Scraped data
    title: str
    meta_description: Optional[str] = None
    h1_tags: List[str] = []
    h2_tags: List[str] = []
    word_count: int = 0
    
    # SEO data (from cleaner.py output)
    seo_data: Dict[str, Any] = {}
    
    # Insights and issues
    insights: Dict[str, List[str]] = {
        "Immediate Action Required": [],
        "Needs Attention": [],
        "Good Practice": []
    }
    
    # Technical data
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    content_hash: Optional[str] = None  # For change detection
    
    # Timestamps
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

# Comparison between snapshots
class SnapshotComparison(BaseModel):
    """Comparison analysis between two snapshots"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    website_id: PyObjectId
    user_id: str
    
    # Snapshots being compared
    baseline_snapshot_id: PyObjectId
    current_snapshot_id: PyObjectId
    
    # High-level changes
    pages_added: int = 0
    pages_removed: int = 0
    pages_modified: int = 0
    
    # SEO changes
    seo_improvements: int = 0
    seo_regressions: int = 0
    new_issues: int = 0
    resolved_issues: int = 0
    
    # Detailed changes
    page_changes: List[Dict[str, Any]] = []
    insight_changes: List[Dict[str, Any]] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

# Competitor analysis
class CompetitorAnalysis(BaseModel):
    """Analysis comparing user's website against competitors"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    primary_website_id: PyObjectId
    competitor_website_ids: List[PyObjectId]
    
    # Analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    primary_snapshot_id: PyObjectId
    competitor_snapshot_ids: List[PyObjectId]
    
    # Comparison results
    competitive_insights: Dict[str, Any] = {}
    opportunities: List[str] = []
    threats: List[str] = []
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}

# API Request/Response Models
class WebsiteCreateRequest(BaseModel):
    """Request to create a new website record"""
    name: str
    base_url: HttpUrl
    website_type: WebsiteType = WebsiteType.PRIMARY
    crawl_frequency_days: int = 7
    max_pages_per_crawl: int = 50
    tags: List[str] = []
    notes: Optional[str] = None

class SnapshotCreateRequest(BaseModel):
    """Request to create a new snapshot"""
    website_id: str
    max_pages: Optional[int] = None

class ComparisonRequest(BaseModel):
    """Request to compare two snapshots"""
    website_id: str
    baseline_snapshot_id: str
    current_snapshot_id: str

class WebsiteListResponse(BaseModel):
    """Response for listing websites"""
    websites: List[Website]
    total: int

class SnapshotListResponse(BaseModel):
    """Response for listing snapshots"""
    snapshots: List[WebsiteSnapshot]
    total: int 