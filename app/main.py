# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import auth, report
from .middleware.auth import AuthMiddleware
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from .database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom auth middleware
app.add_middleware(AuthMiddleware)

# Configure background task handling
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application...")
    app.state.executor = ThreadPoolExecutor(max_workers=2)
    app.state.background_tasks = set()
    
    # Initialize MongoDB
    await init_db()
    
    logger.info("Application initialized successfully")

# Function to track background tasks
def track_background_task(task):
    app.state.background_tasks.add(task)
    task.add_done_callback(lambda t: app.state.background_tasks.remove(t))

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(report.router, prefix="/api", tags=["Data"])

# Include new V2 routes
from .routes import websites_v2
app.include_router(websites_v2.router, prefix="/api/v2", tags=["Websites V2"])

@app.get("/")
async def root():
    return {"message": "Welcome to Scope Labs API"}

# Make track_background_task available to other modules
app.track_background_task = track_background_task
