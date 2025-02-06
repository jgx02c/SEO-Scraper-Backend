# Fast-API

Developed by @jgx02c

## Start Virtural Enviorment
python -m venv venv

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

## Schematic Overview
fastapi-server/
├── app/
│   ├── __init__.py
│   ├── main.py             # Entry point of the application
│   ├── config.py           # Configuration settings
│   ├── models/             # ORM models or data schemas
│   │   ├── __init__.py
│   │   ├── companyModel.py
│   │   ├── promptsModel.py
│   ├── routers/            # API routes grouped by functionality
│   │   ├── __init__.py
│   │   ├── user.py        # For the Front End to connect to the controllers
│   │   ├── data.py        # To Triggure Data creations from Postman
│   ├── services/           # Models for processing and creating via API
│   │   ├── __init__.py
│   │   ├── scrapeOpenAi.py
│   │   ├── createEmbeddings.py
│   │   ├── upsertData.py
│   ├── controllers/           # Controller for processing API functions
│   │   ├── __init__.py
│   │   ├── chatData.py         # Used for Chat + Response.
│   │   ├── addCompany.py       # Insert a New URL to add a Company. Will add All data in Prompts
│   │   ├── getCompanies.py     # Gets all the companies on grid view
│   │   ├── getCompany.py       # Gets the entire Company Data
│   │   ├── deleteCompany.py    # Deletes the Entire Company and All data
│   │   ├── getUser.py          # gets the users company (Leaps and Rebounds)
│   │   ├── getPrompts.py       # Will List all the Promps being used (to gather data)
│   │   ├── savePrompts.py      # Will save all prompts (Delete, edit, add will all be on front end)
│   ├── db/                 # Database connection and session handling
│   │   ├── __init__.py
│   │   ├── mongoConnect.py
│   │   ├── pinecone.py   
│   ├── schemas/            # Pydantic models for request/response validation
│   │   ├── __init__.py
│   │   ├── company.py      # For each Individual Company
│   │   ├── compaanies.py   # For the array of Companies
│   │   ├── prompts.py      # For the prompts
│   ├── utils/              # Utility/helper functions
│   │   ├── __init__.py
│   │   ├── # Nothing as of current         
│   ├── middleware/
│   │   ├── __init__.py
   │   │   ├── # Blank for now 
│   ├── tests/              # Test cases for your application
│   │   ├── __init__.py
│   │   ├── #Blank for now
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
├── Dockerfile              # Dockerfile for containerization
├── README.md               # Project documentation