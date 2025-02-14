from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_route, auth_route, report_route, file_route, business_route, competitor_route, traffic_route, ai_route, actions_route
from middleware.validateJWT import JWTMiddleware

app = FastAPI(title="SEO & Business Intelligence Platform", version="1.0")

# CORS setup for front-end interaction (you can update this list with actual front-end URLs)
origins = [
    "http://localhost:3000",  # React front-end (for example)
    "http://localhost",  # Backend running locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define public endpoints (authentication endpoints that don't require JWT validation)
PUBLIC_ENDPOINTS = [
    "/auth/register",  # Register a new user
    "/auth/login",  # Login and get token
    "/main"
]

# Add JWT Middleware before including the routers
app.add_middleware(JWTMiddleware, public_endpoints=PUBLIC_ENDPOINTS)

# Include routers for different routes
app.include_router(auth_route.router, prefix="/auth", tags=["Authentication"])
app.include_router(user_route.router, prefix="/users", tags=["Users"])
app.include_router(report_route.router, prefix="/reports", tags=["Reports"])
app.include_router(file_route.router, prefix="/files", tags=["Files"])
app.include_router(business_route.router, prefix="/businesses", tags=["Businesses"])
app.include_router(competitor_route.router, prefix="/competitors", tags=["Competitors"])
app.include_router(traffic_route.router, prefix="/traffic", tags=["Traffic"])
app.include_router(ai_route.router, prefix="/ai", tags=["AI & Automation"])
app.include_router(actions_route.router, prefix="/actions", tags=["Actions"])

@app.get("/main")
def read_root():
    return {"message": "Welcome to the SEO & Business Intelligence Platform!"}
