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

## Developement:
uvicorn app.main:app --reload --workers 2 --loop uvloop --http httptools

## Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# app/
# ├── main.py
# ├── config.py
# ├── dependencies.py
# ├── controllers/
# │   ├── __init__.py
# │   ├── auth_controller.py
# │   ├── user_controller.py
# │   └── website_controller.py
# ├── models/
# │   ├── __init__.py
# │   └── user.py
# ├── routes/
# │   ├── __init__.py
# │   ├── auth.py
# │   ├── user.py
# │   └── website.py
# └── utils/
#     ├── __init__.py
#     └── security.py

## Testing Routes

API Key: When making requests with an API key, pass it in the X-API-KEY header.
JWT: When making requests with JWT, pass the token in the Authorization header (Bearer <JWT_TOKEN>)