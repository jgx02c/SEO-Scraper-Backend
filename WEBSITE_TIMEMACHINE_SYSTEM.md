# Website Time-Machine Archiving System

## Overview

The new time-machine archiving system transforms your SEO scraper from a single-analysis tool into a comprehensive website monitoring platform that tracks changes over time and enables competitor analysis.

## 🎯 Key Improvements

### Before (Old System)
- ❌ One-off analysis per URL submission
- ❌ No historical tracking
- ❌ No competitor comparison
- ❌ Data scattered across analysis/webpages/reports collections
- ❌ No master record of websites being tracked

### After (New System)
- ✅ **Master Website Records** - Persistent entities for each domain
- ✅ **Versioned Snapshots** - Time-stamped captures for change tracking
- ✅ **Competitor Management** - Track and compare multiple websites
- ✅ **Historical Analysis** - Compare any two snapshots to see changes
- ✅ **Organized Data Structure** - Clean separation of concerns
- ✅ **Future RAG Ready** - Structured for chatbot integration

## 🏗️ System Architecture

### Data Model Hierarchy

```
User
├── Websites (Master Records)
│   ├── Primary Website (user's main site)
│   ├── Competitor Websites  
│   └── Reference Websites
│
└── Website Snapshots (Versioned Captures)
    ├── Version 1 (Initial baseline)
    ├── Version 2 (Weekly rescan)
    ├── Version 3 (After SEO changes)
    └── ...
    
    └── Page Snapshots (Individual pages within snapshot)
        ├── Homepage data
        ├── About page data
        └── Product pages data
```

### Collections Structure

#### 1. `websites` - Master Website Records
```javascript
{
  "_id": ObjectId,
  "user_id": "user_uuid",
  "domain": "example.com",
  "name": "My Company Website",
  "website_type": "primary|competitor|reference",
  "base_url": "https://example.com",
  "total_snapshots": 5,
  "last_snapshot_at": ISODate,
  "crawl_frequency_days": 7,
  "tags": ["ecommerce", "main-site"],
  "is_active": true
}
```

#### 2. `website_snapshots` - Time-Stamped Captures
```javascript
{
  "_id": ObjectId,
  "website_id": ObjectId,
  "user_id": "user_uuid", 
  "version": 3,
  "snapshot_date": ISODate,
  "scan_status": "completed",
  "pages_scraped": 25,
  "total_insights": 47,
  "critical_issues": 8,
  "warnings": 15,
  "good_practices": 24
}
```

#### 3. `page_snapshots` - Individual Page Data
```javascript
{
  "_id": ObjectId,
  "website_id": ObjectId,
  "snapshot_id": ObjectId,
  "url": "https://example.com/products",
  "title": "Our Products - Example Company",
  "meta_description": "...",
  "seo_data": { /* full scraped data */ },
  "insights": { /* SEO issues found */ },
  "content_hash": "md5_hash_for_change_detection"
}
```

#### 4. `snapshot_comparisons` - Change Analysis
```javascript
{
  "_id": ObjectId,
  "website_id": ObjectId,
  "baseline_snapshot_id": ObjectId,
  "current_snapshot_id": ObjectId,
  "pages_added": 3,
  "pages_removed": 1,
  "pages_modified": 8,
  "page_changes": [/* detailed change data */],
  "insight_changes": [/* SEO improvements/regressions */]
}
```

## 🚀 New API Endpoints

All new endpoints are under `/api/v2/websites`:

### Website Management
```
POST   /api/v2/websites/                    # Create website
GET    /api/v2/websites/                    # List user's websites  
GET    /api/v2/websites/{id}                # Get specific website
```

### Snapshot Management  
```
POST   /api/v2/websites/snapshots           # Create new snapshot
GET    /api/v2/websites/{id}/snapshots      # List website snapshots
GET    /api/v2/websites/snapshots/{id}      # Get specific snapshot
```

### Analysis & Comparison
```
POST   /api/v2/websites/compare             # Compare two snapshots
GET    /api/v2/websites/dashboard/summary   # Dashboard data
```

### Competitor Management
```
GET    /api/v2/websites/competitors         # List competitors
POST   /api/v2/websites/competitors         # Add competitor
```

## 🔄 Migration Strategy

### Automatic Migration
A migration script (`app/utils/migrate_to_v2.py`) converts existing data:

1. **Groups analyses by domain** → Creates master website records
2. **Converts each analysis** → Becomes versioned snapshot  
3. **Preserves all webpage data** → Migrated to page snapshots
4. **Maintains data integrity** → All insights and SEO data preserved

### Running Migration
```bash
# Dry run (safe - shows what would happen)
python -m app.utils.migrate_to_v2

# Execute migration (actually migrates data)  
python -m app.utils.migrate_to_v2 --execute
```

## 💡 Use Cases Enabled

### 1. Time-Machine Analysis
```javascript
// Track how your website changes over time
const snapshots = await fetch('/api/v2/websites/123/snapshots');
const comparison = await fetch('/api/v2/websites/compare', {
  method: 'POST',
  body: JSON.stringify({
    website_id: '123',
    baseline_snapshot_id: 'snapshot_v1', 
    current_snapshot_id: 'snapshot_v5'
  })
});
```

### 2. Competitor Monitoring
```javascript
// Add competitor and track their changes
await fetch('/api/v2/websites/competitors', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Competitor Corp',
    base_url: 'https://competitor.com',
    website_type: 'competitor'
  })
});
```

### 3. Automated Monitoring
- Set `crawl_frequency_days` on websites
- Background jobs create snapshots automatically
- Email alerts when competitors make changes
- Track SEO improvements/regressions over time

### 4. RAG Chatbot Integration (Future)
```javascript
// Load all website data into RAG system
const allData = await fetch('/api/v2/websites/dashboard/summary');
// "What SEO improvements did we make last month?"
// "How do our page titles compare to Competitor X?"
// "Show me all pages with missing meta descriptions"
```

## 🎯 Frontend Integration

### Dashboard Components
```jsx
// Website overview with snapshot history
<WebsiteCard website={website} snapshots={snapshots} />

// Time-machine comparison view  
<SnapshotComparison baseline={v1} current={v5} changes={diff} />

// Competitor tracking dashboard
<CompetitorGrid competitors={competitors} />
```

### Key Frontend Features
- **Timeline View** - Visual snapshot history
- **Change Detection** - Highlight what changed between versions
- **Competitor Dashboard** - Side-by-side comparison
- **Alert System** - Notifications for important changes

## 🔧 Technical Benefits

### 1. **Scalable Architecture**
- Clear separation of master records vs. snapshots
- Efficient querying with proper indexing
- Ready for horizontal scaling

### 2. **Data Integrity** 
- Foreign key relationships via ObjectId references
- Versioned snapshots prevent data loss
- Content hashing for reliable change detection

### 3. **Performance Optimized**
- Aggregated stats at snapshot level
- Indexed queries for fast retrieval
- Background processing for heavy operations

### 4. **Future-Proof**
- Extensible models for new features
- Clean API design for frontend integration
- Ready for RAG/AI integration

## 🚀 Next Steps

1. **Deploy new system** alongside existing (both APIs work)
2. **Run migration** to convert existing data
3. **Update frontend** to use new V2 endpoints  
4. **Add automated scheduling** for regular snapshots
5. **Implement competitor alerts** and change notifications
6. **Integrate RAG chatbot** for natural language queries

The new system transforms your tool from a simple scraper into a comprehensive website intelligence platform! 🎉 