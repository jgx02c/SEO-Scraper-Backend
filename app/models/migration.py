from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MigrationStatus(str, Enum):
    """Status of a migration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationType(str, Enum):
    """Type of migration operation"""
    CREATE_TABLE = "create_table"
    ALTER_TABLE = "alter_table"
    DROP_TABLE = "drop_table"
    CREATE_INDEX = "create_index"
    DROP_INDEX = "drop_index"
    INSERT_DATA = "insert_data"
    UPDATE_DATA = "update_data"
    DELETE_DATA = "delete_data"
    CUSTOM_SQL = "custom_sql"

class Migration(BaseModel):
    """Model for tracking database migrations"""
    id: str = Field(..., description="Unique migration ID (e.g., '001_create_user_profiles')")
    name: str = Field(..., description="Human-readable migration name")
    description: Optional[str] = Field(None, description="Detailed description of what this migration does")
    migration_type: MigrationType = Field(..., description="Type of migration operation")
    
    # SQL content
    up_sql: str = Field(..., description="SQL to apply the migration")
    down_sql: Optional[str] = Field(None, description="SQL to rollback the migration")
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="List of migration IDs this depends on")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = Field(None, description="When migration was applied")
    status: MigrationStatus = Field(default=MigrationStatus.PENDING)
    error_message: Optional[str] = Field(None, description="Error message if migration failed")
    
    # Execution info
    execution_time_ms: Optional[int] = Field(None, description="Time taken to execute migration")
    checksum: Optional[str] = Field(None, description="Checksum of the migration SQL for integrity")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class MigrationHistory(BaseModel):
    """Model for tracking migration execution history"""
    migration_id: str
    executed_at: datetime
    status: MigrationStatus
    execution_time_ms: int
    error_message: Optional[str] = None
    database_version: Optional[str] = None
    applied_by: str = "system"  # Could be user ID or system identifier

class DatabaseSchema(BaseModel):
    """Model representing the current database schema state"""
    version: str = Field(..., description="Current schema version")
    last_migration: Optional[str] = Field(None, description="ID of last applied migration")
    applied_migrations: List[str] = Field(default_factory=list, description="List of applied migration IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TableDefinition(BaseModel):
    """Model for defining database tables"""
    name: str = Field(..., description="Table name")
    columns: List[Dict[str, Any]] = Field(..., description="Column definitions")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="Table constraints")
    indexes: List[Dict[str, Any]] = Field(default_factory=list, description="Table indexes")
    
class MigrationPlan(BaseModel):
    """Model for migration execution plan"""
    pending_migrations: List[Migration] = Field(default_factory=list)
    total_migrations: int = 0
    estimated_time_ms: int = 0
    has_destructive_operations: bool = False
    warnings: List[str] = Field(default_factory=list)

class MigrationResult(BaseModel):
    """Result of migration execution"""
    success: bool
    total_migrations: int = 0
    executed_migrations: List[str] = Field(default_factory=list)
    failed_migrations: List[tuple] = Field(default_factory=list)  # List of (migration_id, error_message) tuples
    execution_time_ms: int = 0
    warnings: List[str] = Field(default_factory=list) 