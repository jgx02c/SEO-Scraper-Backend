from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
import os
import aioredis
import json
from dotenv import load_dotenv 

# Load environment variables from .env file
load_dotenv()

redis_config = os.getenv("redis_config")

class APIKeyJWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_endpoints: list = None, redis_url: str = redis_config, jwt_secret: str = None, jwt_algorithm: str = "HS256"):
        super().__init__(app)
        self.public_endpoints = public_endpoints or []
        self.redis_url = redis_url

        # Load JWT secret
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEY not found in environment variables")

        self.jwt_algorithm = jwt_algorithm

    async def get_redis_connection(self):
        """Establish Redis connection"""
        return await aioredis.from_url(self.redis_url, decode_responses=True)

    async def get_authentication_credentials(self, request: Request):
        """Extracts and returns the API key or JWT token from the request headers."""
        api_key = request.headers.get("x-api-key")
        auth_header = request.headers.get("Authorization")

        if api_key:
            return "api_key", api_key
        elif auth_header and auth_header.startswith("Bearer "):
            return "jwt", auth_header.split(" ")[1]
        else:
            return None, None

    async def authenticate(self, auth_type: str, credentials: str):
        """Handles authentication based on API key or JWT token."""
        if auth_type == "api_key":
            redis = await self.get_redis_connection()
            api_key_data = await redis.get(f"api_key:{credentials}")
            
            if not api_key_data:
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Parse API key data from Redis
            api_key_info = json.loads(api_key_data)

            return {"auth_type": "api_key", "api_key_info": api_key_info}

        elif auth_type == "jwt":
            try:
                payload = jwt.decode(credentials, self.jwt_secret, algorithms=[self.jwt_algorithm])
                return {"auth_type": "jwt", "user": payload}
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.JWTError as e:
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        raise HTTPException(status_code=401, detail="Authentication required. Provide either API key or JWT token")

    async def dispatch(self, request: Request, call_next):
        """Middleware authentication logic."""
        try:
            print(f"Incoming request: {request.url.path}")
            print(f"Headers: {request.headers}")

            # Skip authentication for public endpoints
            if any(request.url.path.startswith(endpoint) for endpoint in self.public_endpoints):
                print("Public endpoint, skipping authentication")
                return await call_next(request)

            # Extract authentication credentials
            auth_type, credentials = await self.get_authentication_credentials(request)
            print("Extracted credentials")
            
            if not credentials:
                raise HTTPException(status_code=401, detail="Authentication required. Provide either API key or JWT token")

            # Authenticate user
            auth_data = await self.authenticate(auth_type, credentials)
            print("Authenticating user auth data")

            # Attach authentication data to request state
            request.state.auth_type = auth_data["auth_type"]
            if "api_key_info" in auth_data:
                request.state.api_key_info = auth_data["api_key_info"]
            if "user" in auth_data:
                request.state.user = auth_data["user"]

            return await call_next(request)

        except HTTPException as e:
            print(f"HTTP Exception: {e.detail}")
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})  # Explicitly return JSON response

        except Exception as e:
            print(f"Unhandled exception: {str(e)}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})  # Explicitly return JSON response
