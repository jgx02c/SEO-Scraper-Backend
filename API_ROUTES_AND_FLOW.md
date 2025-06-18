# SEO Scraper Backend — API Flow & Route Reference

## 🕸️ How the System Works (End-to-End Flow)

### 1. Website Scraping & Snapshot Creation
- **User adds a website** (primary or competitor) via the API.
- **User triggers a snapshot** (scan) for a website.
- **Backend launches a background scan**:
  - Crawls the website, discovers and scrapes all pages.
  - Each page's data (content, SEO, etc.) is loaded into the `page_snapshots` MongoDB collection.
- **After crawling**, the system:
  - **Aggregates page data** to produce a site-wide SEO report.
  - **Stores the report** in the `website_snapshots` MongoDB collection.
  - **Indexes summary data** in SQL for fast analytics and dashboard queries.

### 2. Report Storage & Lookup
- **MongoDB** holds all raw and processed data:
  - `websites` — Master records for each tracked site.
  - `website_snapshots` — Each scan/version of a site (with summary stats/report).
  - `page_snapshots` — All scraped pages for each snapshot.
- **SQL** mirrors summary data for fast dashboard/report lookups and analytics.

### 3. Viewing & Comparing Reports
- **Frontend can:**
  - List all websites and their snapshots.
  - View detailed reports for any snapshot.
  - Compare two snapshots (see what changed, SEO improvements/regressions).
  - Analyze a primary website against competitors (competitive analysis).

---

## 📚 API Route Reference (V2 System)

### Website Management
| Route | Method | Description |
|-------|--------|-------------|
| `/api/v2/websites/` | `GET` | List all websites for the current user. |
| `/api/v2/websites/` | `POST` | Create a new website (primary or competitor). |
| `/api/v2/websites/{website_id}` | `GET` | Get details for a specific website. |
| `/api/v2/websites/{website_id}` | `PATCH` | Update website details. |
| `/api/v2/websites/{website_id}` | `DELETE` | Delete (soft) a website. |

### Snapshot (Scan) Management
| Route | Method | Description |
|-------|--------|-------------|
| `/api/v2/websites/snapshots` | `POST` | Create a new snapshot (scan) for a website. |
| `/api/v2/websites/{website_id}/snapshots` | `GET` | List all snapshots for a website. |
| `/api/v2/websites/snapshots/{snapshot_id}` | `GET` | Get details/report for a specific snapshot. |
| `/api/v2/websites/snapshots/{snapshot_id}/pages` | `GET` | List all pages scraped in a snapshot. |

### Report & Comparison
| Route | Method | Description |
|-------|--------|-------------|
| `/api/v2/websites/compare` | `POST` | Compare two snapshots (detect changes, SEO improvements/regressions). |
| `/api/v2/websites/{website_id}/comparisons` | `GET` | List all comparisons for a website. |
| `/api/v2/websites/{website_id}/competitive-analysis` | `GET` | Analyze a primary website against all competitors. |

### Competitor Management
| Route | Method | Description |
|-------|--------|-------------|
| `/api/v2/websites/competitors` | `GET` | List all competitor websites for the user. |
| `/api/v2/websites/competitors` | `POST` | Add a new competitor website. |

### Dashboard & Analytics
| Route | Method | Description |
|-------|--------|-------------|
| `/api/v2/websites/dashboard/summary` | `GET` | Get summary data for the dashboard (totals, recent snapshots, etc.). |

---

## 📝 Legacy (Deprecated) Endpoints
- `/api/data/analysis/start` — Old one-off analysis (use V2 snapshot creation instead).
- `/api/data/analysis/status` — Old status check (use V2 snapshot status).
- `/api/report/{analysis_id}` — Old report fetch (use V2 snapshot/report endpoints).

---

## 🔎 How to Use (Frontend Flow Example)

1. **Add a Website:**  
   `POST /api/v2/websites/`  
   → Returns website ID.

2. **Trigger a Scan:**  
   `POST /api/v2/websites/snapshots`  
   (with website_id)  
   → Returns snapshot ID.

3. **Check Scan Status / Get Report:**  
   `GET /api/v2/websites/snapshots/{snapshot_id}`  
   → Returns report and summary stats.

4. **List Pages in Snapshot:**  
   `GET /api/v2/websites/snapshots/{snapshot_id}/pages`  
   → Returns all scraped pages.

5. **Compare Snapshots:**  
   `POST /api/v2/websites/compare`  
   (with baseline/current snapshot IDs)  
   → Returns change analysis.

6. **Competitive Analysis:**  
   `GET /api/v2/websites/{website_id}/competitive-analysis`  
   → Returns how the site stacks up against competitors.

---

## 🏷️ Data Model Recap

- **MongoDB:**  
  - `websites` (master records)  
  - `website_snapshots` (site-wide reports)  
  - `page_snapshots` (all scraped pages)
- **SQL:**  
  - Mirrors summary data for fast lookup, analytics, and dashboard queries.

---

## ✅ You Can:
- Scrape and snapshot any website (primary or competitor)
- View all reports and all pages for any snapshot
- Compare any two reports (snapshots) for changes
- Analyze your site against competitors
- Get fast dashboard analytics via SQL 