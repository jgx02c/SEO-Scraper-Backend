from fastapi import FastAPI
from app.middleware.validateApiKeyJWT import APIKeyJWTMiddleware
from app.routers import data_route, processImage_route, prompt_route, service_route, json_routes, user_route, auth_route
from fastapi.middleware.cors import CORSMiddleware

from app.utils.load_keys import load_keys_into_redis

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define public endpoints with complete paths
PUBLIC_ENDPOINTS = [
    "/docs",          # API docs
    "/openapi.json",  # OpenAPI schema
    "/redoc",         # ReDoc documentation
     "/main",   
    "/auth",           # Root endpoint for Login & Signup
]

# Add the middleware first, before including the routers
app.add_middleware(APIKeyJWTMiddleware, public_endpoints=PUBLIC_ENDPOINTS)

# Include routers
app.include_router(user_route.router, prefix="/users", tags=["users"])
app.include_router(processImage_route.router, prefix="/images", tags=["process"])
app.include_router(data_route.router, prefix="/data", tags=["data"])
app.include_router(prompt_route.router, prefix="/prompts", tags=["prompts"])
app.include_router(json_routes.router, prefix="/json", tags=["JSON"])
app.include_router(service_route.router, prefix="/service", tags=["service"])
app.include_router(auth_route.router, prefix="/auth", tags=["auth"])

# FastAPI startup event to call load_keys_into_redis
@app.on_event("startup")
async def startup_event():
    """This function will be executed when the FastAPI app starts."""
    await load_keys_into_redis()

@app.get("/main")
def read_root():
    return {"message": "Welcome to FastAPI Server!"}