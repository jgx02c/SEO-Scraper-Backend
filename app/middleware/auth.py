# app/middleware/auth.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from ..database import supabase
from ..db.supabase import admin_supabase
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle Supabase token verification.
    By default, all routes are protected. Publicly accessible routes
    should be added to the `public_paths` list.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Public paths that don't need authentication.
        # All other routes require authentication by default.
        public_paths = [
            "/api/auth/signin",
            "/api/auth/signup",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        path = request.url.path
        
        # Allow all OPTIONS requests to pass through
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Check if the path is public
        is_public = any(path == public for public in public_paths)
        
        if is_public:
            # If the path is public, proceed without authentication
            return await call_next(request)
        
        # For all other paths, authentication is required.
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("No valid Authorization header found")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract the token
        token = auth_header.split(" ")[1]
        
        try:
            # Use Supabase to validate the token and get the user
            user = supabase.auth.get_user(token)
            
            if not user or not hasattr(user, 'user'):
                logger.warning("Invalid token or user not found")
                raise JWTError("Invalid token")
            
            # Get user profile from Supabase
            profile_response = admin_supabase.table("user_profiles").select("*").eq("auth_user_id", user.user.id).execute()
            
            # We only get the profile, don't try to create or update it
            if not profile_response.data:
                logger.warning(f"No profile found for user {user.user.id}")
                # Continue without a profile - the application should handle this case
            
            # Attach user and profile to request state
            request.state.user = {
                "id": user.user.id,
                "email": user.user.email,
                "roles": user.user.app_metadata.get("roles", ["user"]) if user.user.app_metadata else ["user"],
                "profile": profile_response.data[0] if profile_response.data and isinstance(profile_response.data, list) else None
            }
            
            # Continue with the request
            return await call_next(request)
            
        except JWTError as e:
            logger.warning(f"Authentication error: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication credentials"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error in auth middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during authentication"}
            )
