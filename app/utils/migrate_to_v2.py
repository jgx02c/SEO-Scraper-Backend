"""
Migration script to transition from the old analysis system to the new time-machine system.

This script will:
1. Convert existing analysis records to website master records
2. Convert analysis data to the first snapshot for each website
3. Preserve all existing scraped data in the new format
"""

import asyncio
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any, List

from ..database import db
from ..models.website import WebsiteType, ScanStatus
from ..controllers.website_v2_controller import WebsiteV2Controller

logger = logging.getLogger(__name__)

class MigrationV2:
    def __init__(self):
        self.controller = WebsiteV2Controller()
        
        # Old collections
        self.old_analysis = db.analysis
        self.old_webpages = db.webpages
        self.old_reports = db.reports
        
        # New collections
        self.new_websites = db.websites
        self.new_snapshots = db.website_snapshots
        self.new_pages = db.page_snapshots
        
    async def migrate_all_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migrate all data from old system to new system
        
        Args:
            dry_run: If True, only analyze what would be migrated without making changes
            
        Returns:
            Migration summary
        """
        try:
            logger.info(f"Starting migration (dry_run={dry_run})")
            
            # Get all unique user analyses
            pipeline = [
                {"$group": {
                    "_id": "$user_id",
                    "analyses": {"$push": "$$ROOT"},
                    "count": {"$sum": 1}
                }}
            ]
            
            user_analyses = await self.old_analysis.aggregate(pipeline).to_list(length=None)
            
            migration_summary = {
                "total_users": len(user_analyses),
                "total_analyses": 0,
                "websites_created": 0,
                "snapshots_created": 0,
                "pages_migrated": 0,
                "errors": []
            }
            
            for user_data in user_analyses:
                user_id = user_data["_id"]
                analyses = user_data["analyses"]
                migration_summary["total_analyses"] += len(analyses)
                
                logger.info(f"Migrating {len(analyses)} analyses for user {user_id}")
                
                try:
                    user_summary = await self._migrate_user_data(user_id, analyses, dry_run)
                    migration_summary["websites_created"] += user_summary["websites_created"]
                    migration_summary["snapshots_created"] += user_summary["snapshots_created"]
                    migration_summary["pages_migrated"] += user_summary["pages_migrated"]
                    
                except Exception as e:
                    error_msg = f"Error migrating user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    migration_summary["errors"].append(error_msg)
            
            logger.info("Migration completed")
            logger.info(f"Summary: {migration_summary}")
            
            return migration_summary
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise
    
    async def _migrate_user_data(self, user_id: str, analyses: List[Dict], dry_run: bool) -> Dict[str, int]:
        """Migrate data for a single user"""
        summary = {
            "websites_created": 0,
            "snapshots_created": 0,
            "pages_migrated": 0
        }
        
        # Group analyses by domain to create master website records
        domain_analyses = {}
        for analysis in analyses:
            url = analysis.get("url", "")
            if not url:
                continue
                
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            if domain not in domain_analyses:
                domain_analyses[domain] = []
            domain_analyses[domain].append(analysis)
        
        # Create website records and migrate snapshots
        for domain, domain_analysis_list in domain_analyses.items():
            try:
                # Sort analyses by creation date
                domain_analysis_list.sort(key=lambda x: x.get("created_at", datetime.min))
                
                # Create master website record from first analysis
                first_analysis = domain_analysis_list[0]
                website_id = await self._create_website_record(user_id, domain, first_analysis, dry_run)
                
                if website_id:
                    summary["websites_created"] += 1
                    
                    # Migrate each analysis as a snapshot
                    for i, analysis in enumerate(domain_analysis_list):
                        snapshot_summary = await self._migrate_analysis_to_snapshot(
                            user_id, website_id, analysis, i + 1, dry_run
                        )
                        summary["snapshots_created"] += snapshot_summary["snapshots_created"]
                        summary["pages_migrated"] += snapshot_summary["pages_migrated"]
                        
            except Exception as e:
                logger.error(f"Error migrating domain {domain} for user {user_id}: {str(e)}")
                continue
        
        return summary
    
    async def _create_website_record(self, user_id: str, domain: str, analysis: Dict, dry_run: bool) -> str:
        """Create a master website record from an analysis"""
        try:
            url = analysis.get("url", "")
            if not url:
                return None
                
            # Extract website name from domain
            name = domain.replace('.com', '').replace('.org', '').replace('.net', '').title()
            
            website_doc = {
                "user_id": user_id,
                "domain": domain,
                "name": name,
                "website_type": WebsiteType.PRIMARY.value,
                "base_url": url,
                "crawl_frequency_days": 7,
                "max_pages_per_crawl": 50,
                "tags": [],
                "notes": f"Migrated from analysis {analysis.get('_id')}",
                "created_at": analysis.get("created_at", datetime.utcnow()),
                "updated_at": datetime.utcnow(),
                "total_snapshots": 0,
                "last_snapshot_at": None,
                "is_active": True
            }
            
            if not dry_run:
                # Check if website already exists
                existing = await self.new_websites.find_one({
                    "user_id": user_id,
                    "domain": domain,
                    "is_active": True
                })
                
                if existing:
                    logger.info(f"Website {domain} already exists for user {user_id}")
                    return str(existing["_id"])
                
                result = await self.new_websites.insert_one(website_doc)
                website_id = str(result.inserted_id)
                logger.info(f"Created website record: {domain} -> {website_id}")
                return website_id
            else:
                logger.info(f"[DRY RUN] Would create website: {domain}")
                return "dry_run_website_id"
                
        except Exception as e:
            logger.error(f"Error creating website record: {str(e)}")
            return None
    
    async def _migrate_analysis_to_snapshot(self, user_id: str, website_id: str, analysis: Dict, version: int, dry_run: bool) -> Dict[str, int]:
        """Migrate an analysis record to a snapshot"""
        summary = {"snapshots_created": 0, "pages_migrated": 0}
        
        try:
            analysis_id = analysis.get("_id")
            if not analysis_id:
                return summary
            
            # Determine scan status
            scan_status = analysis.get("scan_status", "completed")
            if scan_status == "error":
                status_enum = ScanStatus.FAILED
            elif scan_status == "completed":
                status_enum = ScanStatus.COMPLETED
            else:
                status_enum = ScanStatus.PENDING
            
            # Create snapshot document
            snapshot_doc = {
                "website_id": website_id if not dry_run else "dry_run_website_id",
                "user_id": user_id,
                "snapshot_date": analysis.get("created_at", datetime.utcnow()),
                "version": version,
                "scan_status": status_enum.value,
                "base_url": analysis.get("url", ""),
                "pages_discovered": analysis.get("total_pages", 0),
                "pages_scraped": analysis.get("pages_scanned", 0),
                "pages_failed": 0,
                "current_step": analysis.get("current_step", "Migrated"),
                "error_message": analysis.get("error_message"),
                "started_at": analysis.get("created_at", datetime.utcnow()),
                "completed_at": analysis.get("completion_time") or analysis.get("last_updated"),
                "total_insights": 0,
                "critical_issues": 0,
                "warnings": 0,
                "good_practices": 0
            }
            
            snapshot_id = None
            if not dry_run:
                result = await self.new_snapshots.insert_one(snapshot_doc)
                snapshot_id = str(result.inserted_id)
                summary["snapshots_created"] = 1
                logger.info(f"Created snapshot v{version} for analysis {analysis_id}")
            else:
                snapshot_id = "dry_run_snapshot_id"
                summary["snapshots_created"] = 1
                logger.info(f"[DRY RUN] Would create snapshot v{version} for analysis {analysis_id}")
            
            # Migrate webpage data to page snapshots
            if snapshot_id:
                pages_migrated = await self._migrate_webpages_to_pages(
                    user_id, website_id, snapshot_id, str(analysis_id), dry_run
                )
                summary["pages_migrated"] = pages_migrated
                
                # Update snapshot stats
                if not dry_run and pages_migrated > 0:
                    await self._update_snapshot_stats(snapshot_id)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error migrating analysis to snapshot: {str(e)}")
            return summary
    
    async def _migrate_webpages_to_pages(self, user_id: str, website_id: str, snapshot_id: str, analysis_id: str, dry_run: bool) -> int:
        """Migrate webpage data to page snapshots"""
        try:
            # Get all webpages for this analysis
            webpages_cursor = self.old_webpages.find({"analysis_id": analysis_id})
            webpages = await webpages_cursor.to_list(length=None)
            
            if not webpages:
                return 0
            
            pages_migrated = 0
            for webpage in webpages:
                try:
                    page_doc = await self._convert_webpage_to_page(
                        user_id, website_id, snapshot_id, webpage
                    )
                    
                    if not dry_run:
                        await self.new_pages.insert_one(page_doc)
                    
                    pages_migrated += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating webpage {webpage.get('url', 'unknown')}: {str(e)}")
                    continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would migrate {pages_migrated} pages for analysis {analysis_id}")
            else:
                logger.info(f"Migrated {pages_migrated} pages for analysis {analysis_id}")
            
            return pages_migrated
            
        except Exception as e:
            logger.error(f"Error migrating webpages: {str(e)}")
            return 0
    
    async def _convert_webpage_to_page(self, user_id: str, website_id: str, snapshot_id: str, webpage: Dict) -> Dict:
        """Convert old webpage format to new page snapshot format"""
        import hashlib
        
        url = webpage.get("url", "")
        parsed_url = urlparse(url)
        
        # Extract SEO data
        title = webpage.get("title", "")
        meta = webpage.get("meta", {})
        meta_description = meta.get("SEO", {}).get("description", "")
        headings = webpage.get("headings", {})
        content = webpage.get("content", "")
        
        # Calculate content hash
        content_hash = hashlib.md5(content.encode()).hexdigest() if content else None
        
        # Extract insights
        insights = webpage.get("insights", {
            "Immediate Action Required": [],
            "Needs Attention": [],
            "Good Practice": []
        })
        
        return {
            "website_id": website_id,
            "snapshot_id": snapshot_id,
            "user_id": user_id,
            "url": url,
            "url_path": parsed_url.path,
            "title": title,
            "meta_description": meta_description,
            "h1_tags": headings.get("h1", []),
            "h2_tags": headings.get("h2", []),
            "word_count": len(content.split()) if content else 0,
            "seo_data": webpage,  # Store full original data
            "insights": insights,
            "content_hash": content_hash,
            "scraped_at": datetime.utcnow()
        }
    
    async def _update_snapshot_stats(self, snapshot_id: str):
        """Update snapshot statistics based on migrated pages"""
        try:
            # Aggregate stats from pages
            pipeline = [
                {"$match": {"snapshot_id": snapshot_id}},
                {"$group": {
                    "_id": None,
                    "total_pages": {"$sum": 1},
                    "total_insights": {
                        "$sum": {
                            "$add": [
                                {"$size": {"$ifNull": ["$insights.Immediate Action Required", []]}},
                                {"$size": {"$ifNull": ["$insights.Needs Attention", []]}},
                                {"$size": {"$ifNull": ["$insights.Good Practice", []]}}
                            ]
                        }
                    },
                    "critical_issues": {"$sum": {"$size": {"$ifNull": ["$insights.Immediate Action Required", []]}}},
                    "warnings": {"$sum": {"$size": {"$ifNull": ["$insights.Needs Attention", []]}}},
                    "good_practices": {"$sum": {"$size": {"$ifNull": ["$insights.Good Practice", []]}}}
                }}
            ]
            
            stats = await self.new_pages.aggregate(pipeline).to_list(length=None)
            
            if stats:
                stat = stats[0]
                await self.new_snapshots.update_one(
                    {"_id": snapshot_id},
                    {"$set": {
                        "pages_scraped": stat.get("total_pages", 0),
                        "total_insights": stat.get("total_insights", 0),
                        "critical_issues": stat.get("critical_issues", 0),
                        "warnings": stat.get("warnings", 0),
                        "good_practices": stat.get("good_practices", 0)
                    }}
                )
                
        except Exception as e:
            logger.error(f"Error updating snapshot stats: {str(e)}")

# CLI interface for running migration
async def run_migration(dry_run: bool = True):
    """Run the migration script"""
    migration = MigrationV2()
    try:
        summary = await migration.migrate_all_data(dry_run=dry_run)
        print("\n" + "="*50)
        print("MIGRATION SUMMARY")
        print("="*50)
        print(f"Total users: {summary['total_users']}")
        print(f"Total analyses: {summary['total_analyses']}")
        print(f"Websites created: {summary['websites_created']}")
        print(f"Snapshots created: {summary['snapshots_created']}")
        print(f"Pages migrated: {summary['pages_migrated']}")
        
        if summary['errors']:
            print(f"\nErrors ({len(summary['errors'])}):")
            for error in summary['errors']:
                print(f"  - {error}")
        
        if dry_run:
            print("\n*** THIS WAS A DRY RUN - NO DATA WAS ACTUALLY MIGRATED ***")
        else:
            print("\n*** MIGRATION COMPLETED ***")
            
    except Exception as e:
        print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("Running migration in DRY RUN mode. Use --execute to actually migrate data.")
    else:
        print("Running migration in EXECUTE mode. Data will be migrated.")
    
    asyncio.run(run_migration(dry_run=dry_run)) 