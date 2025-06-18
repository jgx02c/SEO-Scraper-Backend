-- Migration: 003_create_migration_tracking
-- Description: Create tables to track database migrations and schema versions
-- Type: create_table
-- Depends on: []

-- ===== UP MIGRATION =====
-- @up

-- Create ENUM for migration status
CREATE TYPE migration_status_enum AS ENUM ('pending', 'running', 'completed', 'failed', 'rolled_back');
CREATE TYPE migration_type_enum AS ENUM ('create_table', 'alter_table', 'drop_table', 'create_index', 'drop_index', 'insert_data', 'update_data', 'delete_data', 'custom_sql');

-- Table to track migration definitions and their status
CREATE TABLE IF NOT EXISTS schema_migrations (
    id VARCHAR(255) PRIMARY KEY, -- e.g., '001_create_user_profiles'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    migration_type migration_type_enum NOT NULL,
    
    -- SQL content (stored for reference and rollback)
    up_sql TEXT NOT NULL,
    down_sql TEXT,
    
    -- Dependencies
    depends_on TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Execution tracking
    status migration_status_enum DEFAULT 'pending',
    applied_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_time_ms INTEGER,
    checksum VARCHAR(64), -- SHA256 of the SQL content
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to track migration execution history
CREATE TABLE IF NOT EXISTS migration_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_id VARCHAR(255) NOT NULL REFERENCES schema_migrations(id),
    
    -- Execution details
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status migration_status_enum NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    error_message TEXT,
    
    -- Environment info
    database_version VARCHAR(50),
    applied_by VARCHAR(255) DEFAULT 'system',
    
    -- Rollback info
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    rollback_reason TEXT
);

-- Table to track current database schema state
CREATE TABLE IF NOT EXISTS database_schema (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) NOT NULL,
    last_migration VARCHAR(255) REFERENCES schema_migrations(id),
    applied_migrations TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Only allow one active schema record
    CONSTRAINT only_one_schema_record CHECK (id = gen_random_uuid())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_migrations_status ON schema_migrations(status);
CREATE INDEX IF NOT EXISTS idx_migrations_type ON schema_migrations(migration_type);
CREATE INDEX IF NOT EXISTS idx_migrations_applied_at ON schema_migrations(applied_at);

CREATE INDEX IF NOT EXISTS idx_history_migration_id ON migration_history(migration_id);
CREATE INDEX IF NOT EXISTS idx_history_executed_at ON migration_history(executed_at);
CREATE INDEX IF NOT EXISTS idx_history_status ON migration_history(status);

-- Create updated_at triggers
CREATE TRIGGER update_schema_migrations_updated_at 
    BEFORE UPDATE ON schema_migrations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_database_schema_updated_at 
    BEFORE UPDATE ON database_schema 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert initial schema version
INSERT INTO database_schema (version, applied_migrations) 
VALUES ('1.0.0', ARRAY[]::TEXT[])
ON CONFLICT DO NOTHING;

-- Insert this migration record
INSERT INTO schema_migrations (
    id, name, description, migration_type, up_sql, down_sql, status, applied_at, execution_time_ms
) VALUES (
    '003_create_migration_tracking',
    'Create Migration Tracking',
    'Create tables to track database migrations and schema versions',
    'create_table',
    '-- This migration creates the migration tracking system',
    'DROP TABLE IF EXISTS migration_history CASCADE; DROP TABLE IF EXISTS database_schema CASCADE; DROP TABLE IF EXISTS schema_migrations CASCADE; DROP TYPE IF EXISTS migration_type_enum; DROP TYPE IF EXISTS migration_status_enum;',
    'completed',
    NOW(),
    0
) ON CONFLICT (id) DO NOTHING;

-- ===== DOWN MIGRATION =====
-- @down
DROP TABLE IF EXISTS migration_history CASCADE;
DROP TABLE IF EXISTS database_schema CASCADE;
DROP TABLE IF EXISTS schema_migrations CASCADE;
DROP TYPE IF EXISTS migration_type_enum;
DROP TYPE IF EXISTS migration_status_enum; 