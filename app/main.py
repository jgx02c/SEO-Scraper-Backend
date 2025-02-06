from fastapi import FastAPI
from app.middleware.validateApiKeyJWT import APIKeyJWTMiddleware
from app.routers import user, processImage, data, prompt, json_routes, service
from fastapi.middleware.cors import CORSMiddleware

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
     "/main",              # Root endpoint
 #   "/users/login",   # If you have a login endpoint
  #  "/users/signup"   # If you have a signup endpoint
]

# Add the middleware first, before including the routers
app.add_middleware(APIKeyJWTMiddleware, public_endpoints=PUBLIC_ENDPOINTS)

# Include routers
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(processImage.router, prefix="/images", tags=["process"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(prompt.router, prefix="/prompts", tags=["prompts"])
app.include_router(json_routes.router, prefix="/json", tags=["JSON"])
app.include_router(service.router, prefix="/service", tags=["service"])

@app.get("/main")
def read_root():
    return {"message": "Welcome to FastAPI Server!"}
