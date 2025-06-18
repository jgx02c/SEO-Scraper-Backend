#!/usr/bin/env python3
"""
Script to clean up all database tables before running fresh migrations.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def cleanup_database():
    """Clean up all database tables"""
    try:
        # Read the cleanup SQL
        cleanup_sql_path = Path(__file__).parent.parent / "sql" / "cleanup.sql"
        cleanup_sql = cleanup_sql_path.read_text()
        
        # Connect to the database
        conn = await asyncpg.connect(settings.POSTGRES_URI)
        try:
            # Execute the cleanup SQL
            await conn.execute(cleanup_sql)
            logger.info("Successfully cleaned up database tables")
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error cleaning up database: {str(e)}")
        raise

async def main():
    """Main function"""
    print("🧹 Cleaning up database tables...")
    
    try:
        await cleanup_database()
        print("✅ Database cleanup completed successfully")
        return 0
    except Exception as e:
        print(f"❌ Database cleanup failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 