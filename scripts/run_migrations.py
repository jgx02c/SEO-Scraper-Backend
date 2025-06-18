#!/usr/bin/env python3
"""
Standalone script to run database migrations.

This script can be called from start.sh to ensure migrations are run before the server starts.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.postgres_migration_runner import run_migrations_cli

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to run migrations"""
    print("🔍 Checking for pending database migrations...")
    
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv
    execute = "--execute" in sys.argv
    target = None
    
    # Look for --target argument
    for i, arg in enumerate(sys.argv):
        if arg == "--target" and i + 1 < len(sys.argv):
            target = sys.argv[i + 1]
            break
    
    # Default to dry run unless explicitly told to execute
    if not execute and not dry_run:
        dry_run = True
    
    try:
        await run_migrations_cli(dry_run=dry_run, target=target)
        
        if dry_run:
            print("✅ Migration analysis completed successfully")
            print("💡 Run with --execute to apply migrations")
        else:
            print("✅ All migrations applied successfully")
        return 0
            
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 