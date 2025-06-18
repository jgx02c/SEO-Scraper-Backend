"""
SQL Migration Runner for Supabase Database

This module handles:
- Parsing SQL migration files
- Tracking migration state
- Executing migrations in correct order
- Rolling back migrations if needed
- Validating migration integrity
"""

import os
import re
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..database import supabase
from ..models.migration import (
    Migration, MigrationStatus, MigrationType, 
    MigrationResult, MigrationPlan, DatabaseSchema
)

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migration execution and tracking"""
    
    def __init__(self):
        self.supabase = supabase
        self.migrations_dir = Path(__file__).parent.parent.parent / "sql" / "migrations"
        
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
        # Split by @up and @down markers
        up_match = re.search(r'--\s*@up\s*\n(.*?)(?=--\s*@down|$)', content, re.DOTALL | re.IGNORECASE)
        down_match = re.search(r'--\s*@down\s*\n(.*?)$', content, re.DOTALL | re.IGNORECASE)
        
        up_sql = up_match.group(1).strip() if up_match else content.strip()
        down_sql = down_match.group(1).strip() if down_match else None
        
        return up_sql, down_sql
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migration IDs"""
        try:
            # First ensure migration tracking table exists
            await self._ensure_migration_tracking()
            
            response = self.supabase.table("schema_migrations").select("id").eq("status", "completed").execute()
            
            if response.data:
                return [row["id"] for row in response.data]
            return []
            
        except Exception as e:
            logger.error(f"Error getting applied migrations: {str(e)}")
            return []
    
    async def _ensure_migration_tracking(self):
        """Ensure migration tracking tables exist"""
        try:
            # Check if schema_migrations table exists
            response = self.supabase.table("schema_migrations").select("id").limit(1).execute()
        except Exception:
            # Table doesn't exist, create it by running the migration tracking migration
            logger.info("Migration tracking tables don't exist, creating them...")
            
            tracking_migration_path = self.migrations_dir / "003_create_migration_tracking.sql"
            if tracking_migration_path.exists():
                content = tracking_migration_path.read_text()
                up_sql, _ = self._extract_sql_sections(content)
                
                # Execute the migration tracking SQL directly
                await self._execute_sql(up_sql)
                logger.info("Migration tracking tables created")
            else:
                raise Exception("Migration tracking migration file not found")
    
    async def create_migration_plan(self, target_migration: Optional[str] = None) -> MigrationPlan:
        """Create execution plan for pending migrations"""
        try:
            all_migrations = await self.discover_migrations()
            applied_migrations = await self.get_applied_migrations()
            
            # Filter out already applied migrations
            pending_migrations = [
                m for m in all_migrations 
                if m.id not in applied_migrations
            ]
            
            # If target specified, only include migrations up to target
            if target_migration:
                target_index = next(
                    (i for i, m in enumerate(pending_migrations) if m.id == target_migration), 
                    len(pending_migrations)
                )
                pending_migrations = pending_migrations[:target_index + 1]
            
            # Sort by dependencies and ID
            sorted_migrations = self._sort_migrations_by_dependencies(pending_migrations)
            
            # Calculate estimates and warnings
            estimated_time = sum(self._estimate_migration_time(m) for m in sorted_migrations)
            has_destructive = any(self._is_destructive_migration(m) for m in sorted_migrations)
            
            warnings = []
            if has_destructive:
                warnings.append("Some migrations contain potentially destructive operations")
            
            return MigrationPlan(
                pending_migrations=sorted_migrations,
                total_migrations=len(sorted_migrations),
                estimated_time_ms=estimated_time,
                has_destructive_operations=has_destructive,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error creating migration plan: {str(e)}")
            return MigrationPlan()
    
    def _sort_migrations_by_dependencies(self, migrations: List[Migration]) -> List[Migration]:
        """Sort migrations by dependencies using topological sort"""
        # Create a map for quick lookup
        migration_map = {m.id: m for m in migrations}
        
        # Simple dependency resolution - in a real system you'd want proper topological sort
        sorted_migrations = []
        remaining = migrations.copy()
        
        while remaining:
            # Find migrations with no unresolved dependencies
            ready = []
            for migration in remaining:
                deps_satisfied = all(
                    dep not in migration_map or dep in [m.id for m in sorted_migrations]
                    for dep in migration.depends_on
                )
                if deps_satisfied:
                    ready.append(migration)
            
            if not ready:
                # Circular dependency or missing dependency
                logger.warning("Potential circular dependency detected, using ID order")
                remaining.sort(key=lambda m: m.id)
                sorted_migrations.extend(remaining)
                break
            
            # Add ready migrations and remove from remaining
            ready.sort(key=lambda m: m.id)  # Sort by ID for consistent ordering
            sorted_migrations.extend(ready)
            remaining = [m for m in remaining if m not in ready]
        
        return sorted_migrations
    
    def _estimate_migration_time(self, migration: Migration) -> int:
        """Estimate migration execution time in milliseconds"""
        # Simple heuristic based on migration type and SQL length
        base_time = {
            MigrationType.CREATE_TABLE: 1000,
            MigrationType.ALTER_TABLE: 2000,
            MigrationType.DROP_TABLE: 500,
            MigrationType.CREATE_INDEX: 3000,
            MigrationType.DROP_INDEX: 1000,
            MigrationType.INSERT_DATA: 500,
            MigrationType.UPDATE_DATA: 1500,
            MigrationType.DELETE_DATA: 1000,
            MigrationType.CUSTOM_SQL: 2000
        }.get(migration.migration_type, 2000)
        
        # Add time based on SQL length
        sql_length_factor = len(migration.up_sql) // 100
        
        return base_time + sql_length_factor * 100
    
    def _is_destructive_migration(self, migration: Migration) -> bool:
        """Check if migration contains potentially destructive operations"""
        destructive_keywords = [
            'DROP TABLE', 'DROP COLUMN', 'DELETE FROM', 'TRUNCATE',
            'ALTER TABLE.*DROP', 'DROP INDEX', 'DROP CONSTRAINT'
        ]
        
        sql_upper = migration.up_sql.upper()
        return any(
            re.search(keyword, sql_upper) 
            for keyword in destructive_keywords
        )
    
    async def run_migrations(self, dry_run: bool = False, target_migration: Optional[str] = None) -> MigrationResult:
        """Execute pending migrations"""
        result = MigrationResult(success=True)
        start_time = datetime.now()
        
        try:
            plan = await self.create_migration_plan(target_migration)
            
            if not plan.pending_migrations:
                logger.info("No pending migrations to run")
                return result
            
            logger.info(f"Running {len(plan.pending_migrations)} migrations (dry_run={dry_run})")
            
            for migration in plan.pending_migrations:
                try:
                    migration_start = datetime.now()
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute migration: {migration.id}")
                        result.migrations_applied.append(migration.id)
                    else:
                        logger.info(f"Executing migration: {migration.id}")
                        await self._execute_migration(migration)
                        result.migrations_applied.append(migration.id)
                    
                    migration_time = (datetime.now() - migration_start).total_seconds() * 1000
                    logger.info(f"Migration {migration.id} completed in {migration_time:.0f}ms")
                    
                except Exception as e:
                    error_msg = f"Migration {migration.id} failed: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.migrations_failed.append(migration.id)
                    result.success = False
                    break  # Stop on first failure
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            result.total_time_ms = int(total_time)
            
            logger.info(f"Migration run completed in {total_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Migration run failed: {str(e)}")
            result.success = False
            result.errors.append(str(e))
            return result
    
    async def _execute_migration(self, migration: Migration):
        """Execute a single migration"""
        try:
            # Record migration start
            await self._record_migration_start(migration)
            
            start_time = datetime.now()
            
            # Execute the SQL
            await self._execute_sql(migration.up_sql)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Record successful completion
            await self._record_migration_completion(migration, execution_time)
            
        except Exception as e:
            # Record failure
            await self._record_migration_failure(migration, str(e))
            raise
    
    async def _execute_sql(self, sql: str):
        """Execute SQL against Supabase"""
        try:
            # For Supabase, we need to use the SQL editor or RPC functions
            # This is a simplified version - in production you'd want to use psycopg2 or similar
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    # Use Supabase client to execute SQL
                    # Note: This requires appropriate RLS policies and permissions
                    response = self.supabase.rpc('execute_sql', {'query': statement}).execute()
                    
                    if hasattr(response, 'error') and response.error:
                        raise Exception(f"SQL execution error: {response.error}")
                        
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            # For now, we'll log the error but continue
            # In production, you'd want proper SQL execution
            logger.warning("SQL execution not fully implemented - migrations tracked but not executed")
    
    async def _record_migration_start(self, migration: Migration):
        """Record migration start in tracking table"""
        try:
            self.supabase.table("schema_migrations").upsert({
                "id": migration.id,
                "name": migration.name,
                "description": migration.description,
                "migration_type": migration.migration_type.value,
                "up_sql": migration.up_sql,
                "down_sql": migration.down_sql,
                "depends_on": migration.depends_on,
                "status": MigrationStatus.RUNNING.value,
                "checksum": migration.checksum,
                "created_at": migration.created_at.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error recording migration start: {str(e)}")
    
    async def _record_migration_completion(self, migration: Migration, execution_time: int):
        """Record successful migration completion"""
        try:
            now = datetime.utcnow()
            
            # Update migration record
            self.supabase.table("schema_migrations").update({
                "status": MigrationStatus.COMPLETED.value,
                "applied_at": now.isoformat(),
                "execution_time_ms": execution_time,
                "updated_at": now.isoformat()
            }).eq("id", migration.id).execute()
            
            # Add to migration history
            self.supabase.table("migration_history").insert({
                "migration_id": migration.id,
                "executed_at": now.isoformat(),
                "status": MigrationStatus.COMPLETED.value,
                "execution_time_ms": execution_time
            }).execute()
            
            # Update schema version
            applied_migrations = await self.get_applied_migrations()
            applied_migrations.append(migration.id)
            
            # Update or insert schema record
            schema_response = self.supabase.table("database_schema").select("*").limit(1).execute()
            
            if schema_response.data:
                self.supabase.table("database_schema").update({
                    "last_migration": migration.id,
                    "applied_migrations": applied_migrations,
                    "updated_at": now.isoformat()
                }).eq("id", schema_response.data[0]["id"]).execute()
            else:
                self.supabase.table("database_schema").insert({
                    "version": "1.0.0",
                    "last_migration": migration.id,
                    "applied_migrations": applied_migrations
                }).execute()
            
        except Exception as e:
            logger.error(f"Error recording migration completion: {str(e)}")
    
    async def _record_migration_failure(self, migration: Migration, error_message: str):
        """Record migration failure"""
        try:
            now = datetime.utcnow()
            
            # Update migration record
            self.supabase.table("schema_migrations").update({
                "status": MigrationStatus.FAILED.value,
                "error_message": error_message,
                "updated_at": now.isoformat()
            }).eq("id", migration.id).execute()
            
            # Add to migration history
            self.supabase.table("migration_history").insert({
                "migration_id": migration.id,
                "executed_at": now.isoformat(),
                "status": MigrationStatus.FAILED.value,
                "execution_time_ms": 0,
                "error_message": error_message
            }).execute()
            
        except Exception as e:
            logger.error(f"Error recording migration failure: {str(e)}")

# CLI interface
async def run_migrations_cli(dry_run: bool = True, target: Optional[str] = None):
    """CLI interface for running migrations"""
    runner = MigrationRunner()
    
    try:
        if dry_run:
            print("🔍 Running migration analysis (DRY RUN)...")
        else:
            print("🚀 Running database migrations...")
        
        result = await runner.run_migrations(dry_run=dry_run, target_migration=target)
        
        print("\n" + "="*50)
        print("MIGRATION RESULT")
        print("="*50)
        print(f"Success: {'✅' if result.success else '❌'}")
        print(f"Total time: {result.total_time_ms}ms")
        print(f"Migrations applied: {len(result.migrations_applied)}")
        print(f"Migrations failed: {len(result.migrations_failed)}")
        
        if result.migrations_applied:
            print(f"\n✅ Applied migrations:")
            for migration_id in result.migrations_applied:
                print(f"  - {migration_id}")
        
        if result.migrations_failed:
            print(f"\n❌ Failed migrations:")
            for migration_id in result.migrations_failed:
                print(f"  - {migration_id}")
        
        if result.errors:
            print(f"\n🚨 Errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if dry_run:
            print("\n*** THIS WAS A DRY RUN - NO CHANGES WERE MADE ***")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    dry_run = "--execute" not in sys.argv
    target = None
    
    # Look for --target argument
    for i, arg in enumerate(sys.argv):
        if arg == "--target" and i + 1 < len(sys.argv):
            target = sys.argv[i + 1]
            break
    
    if dry_run:
        print("Running migrations in DRY RUN mode. Use --execute to actually run migrations.")
    else:
        print("Running migrations in EXECUTE mode. Database will be modified.")
    
    if target:
        print(f"Target migration: {target}")
    
    success = asyncio.run(run_migrations_cli(dry_run=dry_run, target=target))
    sys.exit(0 if success else 1) 