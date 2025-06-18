#!/usr/bin/env python3
"""
Database Migration Management CLI

Commands:
  status    - Show migration status
  plan      - Show migration plan
  run       - Run pending migrations
  rollback  - Rollback migrations (future)
  create    - Create new migration file
  validate  - Validate migration files
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.migration_runner import MigrationRunner
from app.models.migration import MigrationType

class MigrationCLI:
    """CLI for managing database migrations"""
    
    def __init__(self):
        self.runner = MigrationRunner()
        self.migrations_dir = Path(__file__).parent.parent / "sql" / "migrations"
    
    async def status(self):
        """Show current migration status"""
        print("📊 Migration Status")
        print("=" * 50)
        
        try:
            all_migrations = await self.runner.discover_migrations()
            applied_migrations = await self.runner.get_applied_migrations()
            
            print(f"Total migrations: {len(all_migrations)}")
            print(f"Applied migrations: {len(applied_migrations)}")
            print(f"Pending migrations: {len(all_migrations) - len(applied_migrations)}")
            
            print("\n📋 Migration List:")
            for migration in all_migrations:
                status = "✅ Applied" if migration.id in applied_migrations else "⏳ Pending"
                print(f"  {migration.id}: {migration.name} - {status}")
            
        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")
            return False
        
        return True
    
    async def plan(self, target=None):
        """Show migration execution plan"""
        print("📋 Migration Plan")
        print("=" * 50)
        
        try:
            plan = await self.runner.create_migration_plan(target)
            
            if not plan.pending_migrations:
                print("✅ No pending migrations")
                return True
            
            print(f"Migrations to run: {plan.total_migrations}")
            print(f"Estimated time: {plan.estimated_time_ms}ms")
            
            if plan.has_destructive_operations:
                print("⚠️  Contains destructive operations")
            
            if plan.warnings:
                print("\n⚠️  Warnings:")
                for warning in plan.warnings:
                    print(f"  - {warning}")
            
            print("\n📝 Execution Order:")
            for i, migration in enumerate(plan.pending_migrations, 1):
                deps = f" (depends on: {', '.join(migration.depends_on)})" if migration.depends_on else ""
                print(f"  {i}. {migration.id}: {migration.name}{deps}")
            
        except Exception as e:
            print(f"❌ Error creating plan: {str(e)}")
            return False
        
        return True
    
    async def run(self, dry_run=False, target=None):
        """Run pending migrations"""
        action = "Analyzing" if dry_run else "Running"
        print(f"🚀 {action} Migrations")
        print("=" * 50)
        
        try:
            result = await self.runner.run_migrations(dry_run=dry_run, target_migration=target)
            
            print(f"\n📊 Results:")
            print(f"Success: {'✅' if result.success else '❌'}")
            print(f"Total time: {result.total_time_ms}ms")
            print(f"Applied: {len(result.migrations_applied)}")
            print(f"Failed: {len(result.migrations_failed)}")
            
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
                print("\n💡 This was a dry run - no changes were made")
                print("Use --execute to apply migrations")
            
            return result.success
            
        except Exception as e:
            print(f"❌ Error running migrations: {str(e)}")
            return False
    
    def create(self, name, migration_type="custom_sql", description=""):
        """Create a new migration file"""
        print(f"📝 Creating Migration: {name}")
        print("=" * 50)
        
        try:
            # Generate migration ID with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            migration_id = f"{timestamp}_{name}"
            filename = f"{migration_id}.sql"
            filepath = self.migrations_dir / filename
            
            # Ensure migrations directory exists
            self.migrations_dir.mkdir(parents=True, exist_ok=True)
            
            # Create migration template
            template = self._create_migration_template(
                migration_id, name, description, migration_type
            )
            
            # Write to file
            filepath.write_text(template)
            
            print(f"✅ Created migration file: {filepath}")
            print(f"📝 Edit the file to add your SQL")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating migration: {str(e)}")
            return False
    
    def _create_migration_template(self, migration_id, name, description, migration_type):
        """Create migration file template"""
        return f"""-- Migration: {migration_id}
-- Description: {description or f"Migration for {name}"}
-- Type: {migration_type}
-- Depends on: []

-- ===== UP MIGRATION =====
-- @up

-- TODO: Add your SQL here
-- Example:
-- CREATE TABLE IF NOT EXISTS example_table (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- ===== DOWN MIGRATION =====
-- @down

-- TODO: Add rollback SQL here
-- Example:
-- DROP TABLE IF EXISTS example_table CASCADE;
"""
    
    async def validate(self):
        """Validate migration files"""
        print("🔍 Validating Migrations")
        print("=" * 50)
        
        try:
            migrations = await self.runner.discover_migrations()
            
            if not migrations:
                print("⚠️  No migrations found")
                return True
            
            errors = []
            warnings = []
            
            for migration in migrations:
                # Check for required fields
                if not migration.up_sql.strip():
                    errors.append(f"{migration.id}: Missing UP SQL")
                
                if not migration.down_sql or not migration.down_sql.strip():
                    warnings.append(f"{migration.id}: Missing DOWN SQL (rollback not possible)")
                
                # Check for dangerous operations without confirmation
                dangerous_keywords = ['DROP TABLE', 'DELETE FROM', 'TRUNCATE']
                sql_upper = migration.up_sql.upper()
                
                for keyword in dangerous_keywords:
                    if keyword in sql_upper and 'IF EXISTS' not in sql_upper:
                        warnings.append(f"{migration.id}: Contains {keyword} without IF EXISTS")
            
            # Check for dependency issues
            migration_ids = {m.id for m in migrations}
            for migration in migrations:
                for dep in migration.depends_on:
                    if dep not in migration_ids:
                        errors.append(f"{migration.id}: Depends on unknown migration '{dep}'")
            
            # Report results
            if errors:
                print(f"❌ Found {len(errors)} errors:")
                for error in errors:
                    print(f"  - {error}")
            
            if warnings:
                print(f"⚠️  Found {len(warnings)} warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
            
            if not errors and not warnings:
                print("✅ All migrations are valid")
            
            return len(errors) == 0
            
        except Exception as e:
            print(f"❌ Error validating migrations: {str(e)}")
            return False

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Database Migration Management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Plan command
    plan_parser = subparsers.add_parser('plan', help='Show migration plan')
    plan_parser.add_argument('--target', help='Target migration ID')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run pending migrations')
    run_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    run_parser.add_argument('--execute', action='store_true', help='Actually execute migrations')
    run_parser.add_argument('--target', help='Target migration ID')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('name', help='Migration name (e.g., "add_user_email")')
    create_parser.add_argument('--type', choices=[t.value for t in MigrationType], 
                              default='custom_sql', help='Migration type')
    create_parser.add_argument('--description', help='Migration description')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate migration files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = MigrationCLI()
    success = True
    
    try:
        if args.command == 'status':
            success = await cli.status()
        
        elif args.command == 'plan':
            success = await cli.plan(target=getattr(args, 'target', None))
        
        elif args.command == 'run':
            # Default to dry run unless explicitly told to execute
            dry_run = not getattr(args, 'execute', False)
            if hasattr(args, 'dry_run') and args.dry_run:
                dry_run = True
            
            success = await cli.run(
                dry_run=dry_run, 
                target=getattr(args, 'target', None)
            )
        
        elif args.command == 'create':
            success = cli.create(
                args.name, 
                getattr(args, 'type', 'custom_sql'),
                getattr(args, 'description', '')
            )
        
        elif args.command == 'validate':
            success = await cli.validate()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 