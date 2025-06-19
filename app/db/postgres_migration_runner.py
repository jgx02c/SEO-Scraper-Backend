"""
PostgreSQL Migration Runner

This module handles database migrations using direct PostgreSQL connection
instead of Supabase REST API for better reliability and performance.
"""

import os
import re
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

import asyncpg
from ..config import settings
from ..models.migration import (
    Migration, MigrationStatus, MigrationType, 
    MigrationResult, MigrationPlan, DatabaseSchema
)

logger = logging.getLogger(__name__)

class PostgreSQLMigrationRunner:
    """Handles database migration execution and tracking using direct PostgreSQL connection"""
    
    def __init__(self):
        self.postgres_uri = settings.POSTGRES_URI
        self.migrations_dir = Path(__file__).parent.parent.parent / "sql" / "migrations"
        
    async def get_connection(self) -> asyncpg.Connection:
        """Get PostgreSQL connection"""
        try:
            conn = await asyncpg.connect(self.postgres_uri)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
        
    async def discover_migrations(self) -> List[Migration]:
        """Discover all migration files and parse them"""
        try:
            migrations = []
            
            if not self.migrations_dir.exists():
                logger.warning(f"Migrations directory not found: {self.migrations_dir}")
                return migrations
            
            # Get all .sql files in migrations directory
            sql_files = sorted(self.migrations_dir.glob("*.sql"))
            
            for sql_file in sql_files:
                try:
                    migration = await self._parse_migration_file(sql_file)
                    if migration:
                        migrations.append(migration)
                except Exception as e:
                    logger.error(f"Error parsing migration file {sql_file}: {str(e)}")
                    continue
            
            logger.info(f"Discovered {len(migrations)} migrations")
            return migrations
            
        except Exception as e:
            logger.error(f"Error discovering migrations: {str(e)}")
            return []
    
    async def _parse_migration_file(self, file_path: Path) -> Optional[Migration]:
        """Parse a single migration file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract metadata from comments
            migration_id = file_path.stem
            name = ""
            description = ""
            migration_type = MigrationType.CUSTOM_SQL
            depends_on = []
            
            # Parse header comments
            lines = content.split('\n')
            for line in lines[:20]:  # Check first 20 lines for metadata
                line = line.strip()
                if line.startswith('-- Migration:'):
                    migration_id = line.replace('-- Migration:', '').strip()
                elif line.startswith('-- Description:'):
                    description = line.replace('-- Description:', '').strip()
                elif line.startswith('-- Type:'):
                    type_str = line.replace('-- Type:', '').strip()
                    try:
                        migration_type = MigrationType(type_str)
                    except ValueError:
                        migration_type = MigrationType.CUSTOM_SQL
                elif line.startswith('-- Depends on:'):
                    deps_str = line.replace('-- Depends on:', '').strip()
                    if deps_str and deps_str != '[]':
                        # Parse dependency list: [dep1, dep2] or dep1,dep2
                        deps_str = deps_str.strip('[]')
                        depends_on = [dep.strip().strip('"\'') for dep in deps_str.split(',') if dep.strip()]
            
            # Extract UP and DOWN SQL
            up_sql, down_sql = self._extract_sql_sections(content)
            
            # Generate checksum
            checksum = hashlib.sha256(content.encode()).hexdigest()
            
            # Use filename as name if not specified
            if not name:
                name = migration_id.replace('_', ' ').title()
            
            return Migration(
                id=migration_id,
                name=name,
                description=description,
                migration_type=migration_type,
                up_sql=up_sql,
                down_sql=down_sql,
                depends_on=depends_on,
                checksum=checksum
            )
            
        except Exception as e:
            logger.error(f"Error parsing migration file {file_path}: {str(e)}")
            return None
    
    def _extract_sql_sections(self, content: str) -> Tuple[str, Optional[str]]:
        """Extract UP and DOWN SQL sections from migration content"""
        # Split by @up and @down markers, also handle DOWN MIGRATION comments
        up_match = re.search(r'--\s*@up\s*\n(.*?)(?=--\s*@down|--\s*=+\s*DOWN\s+MIGRATION|$)', content, re.DOTALL | re.IGNORECASE)
        down_match = re.search(r'--\s*@down\s*\n(.*?)$', content, re.DOTALL | re.IGNORECASE)
        
        up_sql = up_match.group(1).strip() if up_match else content.strip()
        down_sql = down_match.group(1).strip() if down_match else None
        
        return up_sql, down_sql
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migration IDs"""
        try:
            # First ensure migration tracking table exists
            await self._ensure_migration_tracking()
            
            conn = await self.get_connection()
            try:
                result = await conn.fetch(
                    "SELECT id FROM schema_migrations WHERE status = 'completed' ORDER BY executed_at"
                )
                return [row['id'] for row in result]
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting applied migrations: {str(e)}")
            return []
    
    async def _ensure_migration_tracking(self):
        """Ensure migration tracking tables exist"""
        try:
            conn = await self.get_connection()
            try:
                # Check if schema_migrations table exists
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'schema_migrations'
                    )
                """)
                
                if not exists:
                    logger.info("Migration tracking table doesn't exist, creating it...")
                    
                    # Create the migration tracking table
                    await conn.execute("""
                        CREATE TABLE schema_migrations (
                            id VARCHAR(255) PRIMARY KEY,
                            name VARCHAR(500),
                            description TEXT,
                            checksum VARCHAR(64),
                            executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            execution_time INTEGER, -- milliseconds
                            status VARCHAR(50) DEFAULT 'pending',
                            error_message TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    
                    # Create index for better performance
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_schema_migrations_status 
                        ON schema_migrations(status);
                    """)
                    
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_schema_migrations_executed_at 
                        ON schema_migrations(executed_at);
                    """)
                    
                    logger.info("Migration tracking table created successfully")
                    
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error ensuring migration tracking: {str(e)}")
            raise
    
    async def run_migrations(self, dry_run: bool = False, target_migration: Optional[str] = None) -> MigrationResult:
        """Execute pending migrations"""
        start_time = datetime.now()
        
        try:
            all_migrations = await self.discover_migrations()
            applied_migrations = await self.get_applied_migrations()
            
            # Filter out already applied migrations
            pending_migrations = [
                m for m in all_migrations 
                if m.id not in applied_migrations
            ]
            
            # Sort by ID (simple ordering)
            pending_migrations.sort(key=lambda m: m.id)
            
            if not pending_migrations:
                logger.info("No pending migrations to run")
                return MigrationResult(
                    success=True,
                    total_migrations=0,
                    executed_migrations=[],
                    failed_migrations=[],
                    execution_time_ms=0,
                    warnings=[]
                )
            
            logger.info(f"Running {len(pending_migrations)} migrations (dry_run={dry_run})")
            
            executed_migrations = []
            failed_migrations = []
            
            for migration in pending_migrations:
                try:
                    if not dry_run:
                        await self._execute_migration(migration)
                    executed_migrations.append(migration.id)
                    migration_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    logger.info(f"Migration {migration.id} completed in {migration_time}ms")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Migration {migration.id} failed: {error_msg}")
                    failed_migrations.append((migration.id, error_msg))
                    break  # Stop on first failure
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return MigrationResult(
                success=len(failed_migrations) == 0,
                total_migrations=len(pending_migrations),
                executed_migrations=executed_migrations,
                failed_migrations=failed_migrations,
                execution_time_ms=execution_time_ms,
                warnings=[]
            )
            
        except Exception as e:
            logger.error(f"Error running migrations: {str(e)}")
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return MigrationResult(
                success=False,
                total_migrations=0,
                executed_migrations=[],
                failed_migrations=[("general", str(e))],
                execution_time_ms=execution_time_ms,
                warnings=[]
            )
    
    async def _execute_migration(self, migration: Migration):
        """Execute a single migration"""
        start_time = datetime.now()
        
        try:
            # Record migration start
            await self._record_migration_start(migration)
            
            # Execute the SQL
            await self._execute_sql(migration.up_sql)
            
            # Record successful completion
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            await self._record_migration_completion(migration, execution_time)
            
        except Exception as e:
            # Record failure
            await self._record_migration_failure(migration, str(e))
            raise
    
    async def _execute_sql(self, sql: str):
        """Execute SQL statements"""
        conn = await self.get_connection()
        try:
            # Split SQL into individual statements, handling dollar-quoted strings
            statements = self._split_sql_statements(sql)
            for statement in statements:
                if statement.strip():
                    await conn.execute(statement)
                    
        finally:
            await conn.close()
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL into statements, properly handling dollar-quoted strings"""
        statements = []
        current_statement = ""
        in_dollar_quote = False
        dollar_tag = ""
        i = 0
        
        while i < len(sql):
            char = sql[i]
            
            # Check for dollar-quoted string start/end
            if char == '$':
                # Look for dollar quote tag
                tag_start = i
                i += 1
                while i < len(sql) and (sql[i].isalnum() or sql[i] == '_'):
                    i += 1
                if i < len(sql) and sql[i] == '$':
                    tag = sql[tag_start:i+1]
                    if not in_dollar_quote:
                        # Starting a dollar-quoted string
                        in_dollar_quote = True
                        dollar_tag = tag
                        current_statement += sql[tag_start:i+1]
                    elif tag == dollar_tag:
                        # Ending the dollar-quoted string
                        in_dollar_quote = False
                        dollar_tag = ""
                        current_statement += sql[tag_start:i+1]
                    else:
                        # Different dollar tag, treat as regular content
                        current_statement += sql[tag_start:i+1]
                else:
                    # Not a complete dollar tag, treat as regular content
                    current_statement += sql[tag_start:i]
                    i -= 1
            
            # Handle statement separation
            elif char == ';' and not in_dollar_quote:
                current_statement += char
                statements.append(current_statement.strip())
                current_statement = ""
            else:
                current_statement += char
            
            i += 1
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return [stmt for stmt in statements if stmt]
    
    async def _record_migration_start(self, migration: Migration):
        """Record migration start in tracking table"""
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    INSERT INTO schema_migrations (id, name, description, checksum, status)
                    VALUES ($1, $2, $3, $4, 'running')
                    ON CONFLICT (id) DO UPDATE SET
                        status = 'running',
                        updated_at = NOW()
                """, migration.id, migration.name, migration.description, migration.checksum)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error recording migration start: {str(e)}")
    
    async def _record_migration_completion(self, migration: Migration, execution_time: int):
        """Record successful migration completion"""
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    UPDATE schema_migrations 
                    SET status = 'completed',
                        executed_at = NOW(),
                        execution_time = $2,
                        updated_at = NOW()
                    WHERE id = $1
                """, migration.id, execution_time)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error recording migration completion: {str(e)}")
    
    async def _record_migration_failure(self, migration: Migration, error_message: str):
        """Record migration failure"""
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    UPDATE schema_migrations 
                    SET status = 'failed',
                        error_message = $2,
                        updated_at = NOW()
                    WHERE id = $1
                """, migration.id, error_message)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error recording migration failure: {str(e)}")


async def run_migrations_cli(dry_run: bool = True, target: Optional[str] = None):
    """CLI function to run migrations"""
    runner = PostgreSQLMigrationRunner()
    result = await runner.run_migrations(dry_run=dry_run, target_migration=target)
    
    print("\n" + "="*50)
    print("MIGRATION RESULT")
    print("="*50)
    print(f"Success: {'✅' if result.success else '❌'}")
    print(f"Total time: {result.execution_time_ms}ms")
    print(f"Migrations applied: {len(result.executed_migrations)}")
    print(f"Migrations failed: {len(result.failed_migrations)}")
    
    if result.executed_migrations:
        print(f"\n✅ Applied migrations:")
        for migration_id in result.executed_migrations:
            print(f"  - {migration_id}")
    
    if result.failed_migrations:
        print(f"\n❌ Failed migrations:")
        for migration_id, error in result.failed_migrations:
            print(f"  - {migration_id}: {error}")
    
    if result.success:
        print("✅ All migrations applied successfully")
    else:
        print("❌ Some migrations failed")
        raise Exception("Migration failed") 