# SQL Migration System

This directory contains the database migration system for managing Supabase schema changes using Pydantic models for tracking and validation.

## 📁 Directory Structure

```
sql/
├── migrations/           # Migration files
│   ├── 001_create_user_profiles.sql
│   ├── 002_create_website_tracking.sql
│   ├── 003_create_migration_tracking.sql
│   └── ...
└── README.md            # This file
```

## 🏗️ Migration File Format

Each migration file follows a standardized format:

```sql
-- Migration: 001_create_user_profiles
-- Description: Create user profiles table for storing user information
-- Type: create_table
-- Depends on: []

-- ===== UP MIGRATION =====
-- @up
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- ... table definition
);

-- ===== DOWN MIGRATION =====
-- @down
DROP TABLE IF EXISTS user_profiles CASCADE;
```

### Header Metadata

- **Migration**: Unique ID (matches filename)
- **Description**: Human-readable description
- **Type**: Migration type enum (`create_table`, `alter_table`, `drop_table`, `create_index`, `drop_index`, `insert_data`, `update_data`, `delete_data`, `custom_sql`)
- **Depends on**: Array of migration IDs this migration depends on

### SQL Sections

- **@up**: SQL to apply the migration
- **@down**: SQL to rollback the migration (optional)

## 🚀 Running Migrations

### Automatic (via start.sh)
Migrations run automatically when starting the server:

```bash
./start.sh
```

### Manual Execution

```bash
# Dry run (analyze what would happen)
python3.9 scripts/run_migrations.py --dry-run

# Execute migrations
python3.9 scripts/run_migrations.py --execute

# Run specific migration
python3.9 scripts/run_migrations.py --execute --target 002_create_website_tracking
```

### Programmatic Usage

```python
from app.db.migration_runner import MigrationRunner

runner = MigrationRunner()

# Get migration plan
plan = await runner.create_migration_plan()

# Execute migrations
result = await runner.run_migrations(dry_run=False)
```

## 📊 Migration Tracking

The system tracks migrations in Supabase tables:

### `schema_migrations`
Stores migration definitions and their execution status:
```sql
id                  | VARCHAR(255) | Primary key (migration ID)
name                | VARCHAR(255) | Human-readable name
description         | TEXT         | Migration description
migration_type      | ENUM         | Type of migration
up_sql              | TEXT         | SQL to apply migration
down_sql            | TEXT         | SQL to rollback migration
depends_on          | TEXT[]       | Dependencies
status              | ENUM         | pending|running|completed|failed|rolled_back
applied_at          | TIMESTAMPTZ  | When migration was applied
execution_time_ms   | INTEGER      | Execution time
checksum            | VARCHAR(64)  | SHA256 of migration content
```

### `migration_history`
Tracks execution history:
```sql
id                  | UUID         | Primary key
migration_id        | VARCHAR(255) | Reference to migration
executed_at         | TIMESTAMPTZ  | Execution timestamp
status              | ENUM         | Execution status
execution_time_ms   | INTEGER      | Time taken
error_message       | TEXT         | Error if failed
```

### `database_schema`
Tracks current schema state:
```sql
id                  | UUID         | Primary key
version             | VARCHAR(50)  | Schema version
last_migration      | VARCHAR(255) | Last applied migration
applied_migrations  | TEXT[]       | All applied migration IDs
```

## 🎯 Migration Types

### CREATE_TABLE
```sql
-- Type: create_table
CREATE TABLE new_table (
    id UUID PRIMARY KEY,
    name VARCHAR(255)
);
```

### ALTER_TABLE
```sql
-- Type: alter_table
ALTER TABLE existing_table 
ADD COLUMN new_column VARCHAR(255);
```

### CREATE_INDEX
```sql
-- Type: create_index
CREATE INDEX idx_table_column ON table_name(column_name);
```

### INSERT_DATA
```sql
-- Type: insert_data
INSERT INTO lookup_table (code, name) VALUES 
('US', 'United States'),
('CA', 'Canada');
```

## 🔄 Best Practices

### 1. **Always Include Rollback**
```sql
-- @up
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- @down
ALTER TABLE users DROP COLUMN email;
```

### 2. **Use IF NOT EXISTS**
```sql
-- @up
CREATE TABLE IF NOT EXISTS new_table (...);
CREATE INDEX IF NOT EXISTS idx_name ON table(column);
```

### 3. **Handle Dependencies**
```sql
-- Depends on: [001_create_users, 002_create_profiles]
```

### 4. **Test Migrations**
Always test migrations in development:
```bash
# Test with dry run first
python3.9 scripts/run_migrations.py --dry-run

# Then execute
python3.9 scripts/run_migrations.py --execute
```

### 5. **Descriptive Names**
Use clear, descriptive migration names:
- ✅ `005_add_user_email_verification`
- ✅ `006_create_website_snapshots_table`
- ❌ `005_misc_changes`
- ❌ `006_fix_stuff`

## 🛡️ Safety Features

### Checksum Validation
Each migration has a SHA256 checksum to detect changes:
```python
# Prevents running modified migrations
checksum = hashlib.sha256(content.encode()).hexdigest()
```

### Dependency Resolution
Migrations run in correct order based on dependencies:
```sql
-- This will run after 001 and 002
-- Depends on: [001_create_users, 002_create_profiles]
```

### Rollback Support
Each migration can include rollback SQL:
```sql
-- @down
DROP TABLE IF EXISTS new_table CASCADE;
```

### Row Level Security (RLS)
All tables include RLS policies:
```sql
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own data" ON table_name
    FOR SELECT USING (auth.uid() = user_id);
```

## 🔧 Troubleshooting

### Migration Failed
```bash
# Check migration status
python3.9 scripts/run_migrations.py --dry-run

# Check logs for specific error
tail -f logs/migration.log
```

### Reset Migration State
```sql
-- Mark migration as pending to retry
UPDATE schema_migrations 
SET status = 'pending', error_message = NULL 
WHERE id = 'migration_id';
```

### Manual SQL Execution
For complex migrations, you may need to run SQL manually in Supabase dashboard, then mark as completed:

```sql
-- After manual execution
UPDATE schema_migrations 
SET status = 'completed', applied_at = NOW() 
WHERE id = 'migration_id';
```

## 📈 Future Enhancements

- **Rollback Command**: Automated rollback functionality
- **Migration Branches**: Support for feature branch migrations
- **Data Validation**: Post-migration data validation
- **Performance Monitoring**: Track migration performance over time
- **Backup Integration**: Automatic backups before destructive operations

## 🔗 Related Files

- `app/models/migration.py` - Pydantic models for migrations
- `app/db/migration_runner.py` - Migration execution engine
- `scripts/run_migrations.py` - CLI interface
- `start.sh` - Automatic migration execution 