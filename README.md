# Fast-API Scraper

Developed by @jgx02c 

## Starting Redis Server On Mac

brew services start redis

## Starting Redis Server On Windows



## Check to see if Redis is Running
redis-cli ping

## Start Virtural Enviorment
python3.9 -m venv venv

# Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

## Install Rquirements
pip install -r requirements.txt

# Deactivate Venv
deactivate

# Save Additional Dependencies:
pip freeze > requirements.txt

## Starting Fast API Server
uvicorn app.main:app --reload

## Schematic Overiew
fastapi-server/
├── app/
│   ├── __init__.py
│   ├── main.py             # Entry point of the application
│   ├── config.py           # Configuration settings (env variables, API keys, etc.)
│   ├── models/             # ORM models or data schemas
│   │   ├── __init__.py
│   │   ├── userModel.py
│   │   ├── businessModel.py
│   │   ├── reportModel.py
│   │   ├── fileModel.py
│   │   ├── auditModel.py
│   ├── routers/            # API routes grouped by functionality
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── business.py
│   │   ├── report.py
│   │   ├── file.py
│   │   ├── auth.py
│   │   ├── chatbot.py
│   │   ├── seoAudit.py
│   ├── services/           # Business logic & API processing functions
│   │   ├── __init__.py
│   │   ├── seoAuditService.py  # Handles SEO audits
│   │   ├── reportService.py    # Processes audit reports
│   │   ├── businessService.py  # Handles business details
│   │   ├── userService.py      # Handles user-related operations
│   │   ├── chatbotService.py   # AI chatbot logic
│   │   ├── fileService.py      # Handles file uploads & storage
│   ├── controllers/           # Controller for processing API functions
│   │   ├── __init__.py
│   │   ├── processAudit.py      # Runs SEO audit processes
│   │   ├── getReports.py        # Fetches generated reports
│   │   ├── deleteReport.py      # Deletes an audit report
│   │   ├── getBusiness.py       # Fetches business details
│   │   ├── editBusiness.py      # Updates business data
│   │   ├── getUserProfile.py    # Retrieves user details
│   │   ├── editUserProfile.py   # Updates user profile
│   │   ├── getFile.py           # Fetches uploaded files
│   │   ├── deleteFile.py        # Deletes uploaded files
│   ├── db/                 # Database connection and session handling
│   │   ├── __init__.py
│   │   ├── mongoConnect.py       # MongoDB connection
│   │   ├── redisCache.py         # Redis cache handling
│   ├── schemas/            # Pydantic models for request/response validation
│   │   ├── __init__.py
│   │   ├── userSchema.py
│   │   ├── businessSchema.py
│   │   ├── reportSchema.py
│   │   ├── fileSchema.py
│   │   ├── seoAuditSchema.py
│   ├── utils/              # Utility/helper functions
│   │   ├── __init__.py
│   │   ├── jwt.py           # JWT authentication helper
│   │   ├── seoHelper.py      # SEO-related helper functions
│   │   ├── redisHelper.py    # Redis cache management
│   │   ├── fileHelper.py     # File handling utilities
│   ├── middleware/         # Middleware for request validation
│   │   ├── __init__.py
│   │   ├── validateJWT.py    # Validates JWT tokens
│   │   ├── validateAPIKey.py # Validates API keys
│   ├── tests/              # Test cases for your application
│   │   ├── __init__.py
│   │   ├── test_user.py
│   │   ├── test_business.py
│   │   ├── test_report.py
│   │   ├── test_seoAudit.py  # Tests for SEO audits
│   │   ├── test_redis.py     # Tests for Redis-related functionality
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
├── Dockerfile              # Dockerfile for containerization
├── README.md               # Project documentation


## Testing Routes

API Key: When making requests with an API key, pass it in the X-API-KEY header.
JWT: When making requests with JWT, pass the token in the Authorization header (Bearer <JWT_TOKEN>)