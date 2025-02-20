import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import auth, user, website
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

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

# Configure background task handling
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application...")
    app.state.executor = ThreadPoolExecutor(max_workers=2)
    app.state.background_tasks = set()
    logger.info("ThreadPoolExecutor initialized with 2 workers")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    app.state.executor.shutdown(wait=True)
    for task in app.state.background_tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*app.state.background_tasks, return_exceptions=True)
    logger.info("Shutdown complete")

# Function to track background tasks
def track_background_task(task):
    app.state.background_tasks.add(task)
    task.add_done_callback(lambda t: app.state.background_tasks.remove(t))

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(website.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Scope Labs API"}

# Make track_background_task available to other modules
app.track_background_task = track_background_task
