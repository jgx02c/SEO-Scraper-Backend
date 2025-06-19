# SEO Scraper Backend - Postman Collection Guide

## 📦 What's Included

This Postman collection contains **all API endpoints** for the SEO Scraper Backend, organized into the following folders:

### 1. **Authentication**
- Sign Up
- Sign In (with automatic token extraction)
- Forgot Password
- Reset Password

### 2. **Website Management (V2)**
- Create Website
- List All Websites
- List Websites by Type
- Get Website by ID

### 3. **Snapshot Management**
- Create Snapshot (trigger website crawling)
- List Website Snapshots
- Get Snapshot Details
- Get Snapshot Pages

### 4. **Comparison & Analysis**
- Compare Snapshots
- Get Website Comparisons
- Competitive Analysis

### 5. **Competitor Management**
- List Competitors
- Add Competitor

### 6. **Dashboard**
- Dashboard Summary

### 7. **Legacy Endpoints (Deprecated)**
- Included for backward compatibility

### 8. **Utility**
- Health Check

## 🚀 How to Use

### Step 1: Import the Collection
1. Open Postman
2. Click **Import** in the top left
3. Select the `SEO-Scraper-Backend-Postman-Collection.json` file
4. The collection will be imported with all endpoints

### Step 2: Set Up Environment Variables
The collection uses two main variables:
- `base_url`: Set this to your API base URL (default: `http://localhost:8000`)
- `auth_token`: This will be automatically set after signing in

#### To set up environment:
1. Click on **Environments** in Postman
2. Create a new environment (e.g., "SEO Scraper Local")
3. Add the variable:
   - `base_url` = `http://localhost:8000` (or your server URL)

### Step 3: Authentication Flow
1. **Sign Up**: Create a new user account - this will automatically create both the auth user AND user profile
2. **Sign In**: Use your credentials - the token will be automatically extracted and stored
   - If no profile exists (for existing users), one will be created automatically
3. All subsequent requests will use the token for authentication

### Step 4: Basic Workflow
1. **Create a Website**: Add your primary website or competitors
2. **Create Snapshot**: Trigger a crawl/scan of the website
3. **Get Snapshot Details**: Check the scan results and SEO analysis
4. **Compare Snapshots**: Compare different scans to see improvements/changes
5. **Competitive Analysis**: Analyze your site against competitors

## 🔧 Configuration

### Base URL Options
- **Local Development**: `http://localhost:8000`
- **Production**: Replace with your production API URL

### Authentication
The collection is configured to automatically:
- Extract the access token from successful sign-in responses
- Include the token in all authenticated requests
- Use Bearer token authentication

## 📝 Example Variables to Replace

When using the requests, replace these placeholder values:
- `website_id_here` → Actual website ID from your database
- `snapshot_id_here` → Actual snapshot ID from your database
- `older_snapshot_id` → ID of baseline snapshot for comparison
- `newer_snapshot_id` → ID of current snapshot for comparison
- `analysis_id_here` → Legacy analysis ID (deprecated endpoints)

## 🎯 Quick Start Sequence

1. **Health Check** → Verify API is running
2. **Sign Up** → Create account
3. **Sign In** → Get authenticated
4. **Create Website** → Add your website
5. **Create Snapshot** → Start scanning
6. **Get Snapshot Details** → View results
7. **Dashboard Summary** → See overview

## 📚 Response Examples

### Successful Sign In Response
```json
{
  "user": {
    "id": "7a080651-15a7-4401-ac18-309fbff0c145",
    "email": "user@example.com",
    ...
  },
  "session": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600,
    "token_type": "bearer"
  },
  "profile": {
    "id": "...",
    "auth_user_id": "7a080651-15a7-4401-ac18-309fbff0c145",
    "email": "user@example.com",
    "name": "John Doe",
    "company": "Example Corp",
    "role": "Marketing Manager",
    "plan_type": "free",
    "subscription_status": "active",
    "has_completed_onboarding": false,
    "analyses_count": 0,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Website Creation Response
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "My Website",
  "domain": "example.com",
  "website_type": "primary",
  "base_url": "https://example.com",
  "created_at": "2024-01-01T00:00:00",
  ...
}
```

## 🔍 Tips

1. **Use the Test Scripts**: The Sign In request has a test script that automatically saves your auth token
2. **Check Descriptions**: Each request has detailed descriptions explaining what it does
3. **Use Variables**: Replace placeholder IDs with actual values from your responses
4. **Environment Switching**: You can create multiple environments for different deployment stages

## 🛠️ Troubleshooting

- **401 Unauthorized**: Make sure you're signed in and the auth token is set
- **404 Not Found**: Verify the base_url is correct and the API is running
- **500 Internal Server Error**: Check the API logs for backend issues
- **Invalid ObjectId**: Make sure you're using valid MongoDB ObjectId format for IDs
- **"User profile not found"**: This should be automatically resolved now - the signup and signin endpoints will create profiles automatically
- **Profile creation issues**: The system will attempt to create profiles during both signup and signin, so existing users should be covered

---

Happy API testing! 🚀 