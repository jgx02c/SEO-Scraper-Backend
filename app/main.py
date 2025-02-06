from fastapi import FastAPI
from app.routers import user, data
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
 
# Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without any middleware restrictions
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(data.router, prefix="/data", tags=["data"])

@app.get("/main")
def read_root():
    return {"message": "Welcome to FastAPI Server!"}
