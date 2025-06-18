-- Drop all existing tables and functions
-- Drop tables in dependency order (child tables first)
DROP TABLE IF EXISTS snapshot_comparisons CASCADE;
DROP TABLE IF EXISTS page_snapshots_summary CASCADE;
DROP TABLE IF EXISTS website_snapshots CASCADE;
DROP TABLE IF EXISTS websites CASCADE;
DROP TABLE IF EXISTS migration_history CASCADE;
DROP TABLE IF EXISTS database_schema CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS schema_migrations CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS migration_status_enum CASCADE;
DROP TYPE IF EXISTS migration_type_enum CASCADE;
DROP TYPE IF EXISTS scan_status_enum CASCADE;
DROP TYPE IF EXISTS website_type_enum CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE; 