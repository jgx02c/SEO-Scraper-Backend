-- Migration: 002_create_website_tracking
-- Description: Create tables for website tracking and time-machine functionality
-- Type: create_table
-- Depends on: [001_create_user_profiles]

-- ===== UP MIGRATION =====
-- @up

-- Create ENUM types for better data integrity
CREATE TYPE website_type_enum AS ENUM ('primary', 'competitor', 'reference');
CREATE TYPE scan_status_enum AS ENUM ('pending', 'crawling', 'processing', 'completed', 'failed');

-- Master websites table (SQL mirror of MongoDB websites collection)
CREATE TABLE IF NOT EXISTS websites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User relationship
    user_id UUID NOT NULL REFERENCES user_profiles(auth_user_id) ON DELETE CASCADE,
    
    -- Website identification
    domain VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    website_type website_type_enum NOT NULL DEFAULT 'primary',
    base_url TEXT NOT NULL,
    
    -- MongoDB reference
    mongo_id VARCHAR(24) UNIQUE, -- ObjectId from MongoDB
    
    -- Configuration
    crawl_frequency_days INTEGER DEFAULT 7,
    max_pages_per_crawl INTEGER DEFAULT 50,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    notes TEXT,
    
    -- Tracking info
    total_snapshots INTEGER DEFAULT 0,
    last_snapshot_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, domain, is_active)
);

-- Website snapshots table (SQL mirror of MongoDB snapshots collection)
CREATE TABLE IF NOT EXISTS website_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(auth_user_id) ON DELETE CASCADE,
    
    -- MongoDB reference
    mongo_id VARCHAR(24) UNIQUE, -- ObjectId from MongoDB
    
    -- Snapshot metadata
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER NOT NULL,
    scan_status scan_status_enum DEFAULT 'pending',
    
    -- Scan details
    base_url TEXT NOT NULL,
    pages_discovered INTEGER DEFAULT 0,
    pages_scraped INTEGER DEFAULT 0,
    pages_failed INTEGER DEFAULT 0,
    scan_duration_seconds INTEGER,
    
    -- Status tracking
    current_step TEXT DEFAULT 'Initializing',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Summary stats (aggregated from page data)
    total_insights INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    good_practices INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(website_id, version)
);

-- Page snapshots summary table (key metrics from MongoDB page_snapshots)
CREATE TABLE IF NOT EXISTS page_snapshots_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES website_snapshots(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(auth_user_id) ON DELETE CASCADE,
    
    -- MongoDB reference
    mongo_id VARCHAR(24) UNIQUE, -- ObjectId from MongoDB
    
    -- Page identification
    url TEXT NOT NULL,
    url_path TEXT,
    page_type VARCHAR(50) DEFAULT 'page',
    
    -- Key SEO metrics
    title TEXT,
    meta_description TEXT,
    word_count INTEGER DEFAULT 0,
    h1_count INTEGER DEFAULT 0,
    h2_count INTEGER DEFAULT 0,
    
    -- Insights summary
    critical_issues_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    good_practices_count INTEGER DEFAULT 0,
    
    -- Technical data
    response_time_ms INTEGER,
    status_code INTEGER,
    content_hash VARCHAR(32), -- MD5 hash for change detection
    
    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(snapshot_id, url)
);

-- Snapshot comparisons table
CREATE TABLE IF NOT EXISTS snapshot_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(auth_user_id) ON DELETE CASCADE,
    baseline_snapshot_id UUID NOT NULL REFERENCES website_snapshots(id) ON DELETE CASCADE,
    current_snapshot_id UUID NOT NULL REFERENCES website_snapshots(id) ON DELETE CASCADE,
    
    -- MongoDB reference
    mongo_id VARCHAR(24) UNIQUE,
    
    -- High-level changes
    pages_added INTEGER DEFAULT 0,
    pages_removed INTEGER DEFAULT 0,
    pages_modified INTEGER DEFAULT 0,
    
    -- SEO changes
    seo_improvements INTEGER DEFAULT 0,
    seo_regressions INTEGER DEFAULT 0,
    new_issues INTEGER DEFAULT 0,
    resolved_issues INTEGER DEFAULT 0,
    
    -- Summary scores
    overall_score_change DECIMAL(5,2), -- -100 to +100
    performance_impact VARCHAR(20), -- 'positive', 'negative', 'neutral'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CHECK (baseline_snapshot_id != current_snapshot_id),
    UNIQUE(baseline_snapshot_id, current_snapshot_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_websites_user_id ON websites(user_id);
CREATE INDEX IF NOT EXISTS idx_websites_domain ON websites(domain);
CREATE INDEX IF NOT EXISTS idx_websites_type ON websites(website_type);
CREATE INDEX IF NOT EXISTS idx_websites_mongo_id ON websites(mongo_id);

CREATE INDEX IF NOT EXISTS idx_snapshots_website_id ON website_snapshots(website_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_user_id ON website_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON website_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_snapshots_status ON website_snapshots(scan_status);
CREATE INDEX IF NOT EXISTS idx_snapshots_version ON website_snapshots(website_id, version);
CREATE INDEX IF NOT EXISTS idx_snapshots_mongo_id ON website_snapshots(mongo_id);

CREATE INDEX IF NOT EXISTS idx_pages_snapshot_id ON page_snapshots_summary(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_pages_website_id ON page_snapshots_summary(website_id);
CREATE INDEX IF NOT EXISTS idx_pages_url ON page_snapshots_summary(url);
CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON page_snapshots_summary(content_hash);
CREATE INDEX IF NOT EXISTS idx_pages_mongo_id ON page_snapshots_summary(mongo_id);

CREATE INDEX IF NOT EXISTS idx_comparisons_website_id ON snapshot_comparisons(website_id);
CREATE INDEX IF NOT EXISTS idx_comparisons_baseline ON snapshot_comparisons(baseline_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_comparisons_current ON snapshot_comparisons(current_snapshot_id);

-- Create updated_at triggers
CREATE TRIGGER update_websites_updated_at 
    BEFORE UPDATE ON websites 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_website_snapshots_updated_at 
    BEFORE UPDATE ON website_snapshots 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE websites ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE page_snapshots_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE snapshot_comparisons ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for websites
CREATE POLICY "Users can view own websites" ON websites
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own websites" ON websites
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own websites" ON websites
    FOR UPDATE USING (auth.uid() = user_id);

-- Create RLS policies for snapshots
CREATE POLICY "Users can view own snapshots" ON website_snapshots
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own snapshots" ON website_snapshots
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own snapshots" ON website_snapshots
    FOR UPDATE USING (auth.uid() = user_id);

-- Create RLS policies for page summaries
CREATE POLICY "Users can view own page summaries" ON page_snapshots_summary
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own page summaries" ON page_snapshots_summary
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create RLS policies for comparisons
CREATE POLICY "Users can view own comparisons" ON snapshot_comparisons
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own comparisons" ON snapshot_comparisons
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ===== DOWN MIGRATION =====
-- @down
DROP TABLE IF EXISTS snapshot_comparisons CASCADE;
DROP TABLE IF EXISTS page_snapshots_summary CASCADE;
DROP TABLE IF EXISTS website_snapshots CASCADE;
DROP TABLE IF EXISTS websites CASCADE;
DROP TYPE IF EXISTS scan_status_enum;
DROP TYPE IF EXISTS website_type_enum; 