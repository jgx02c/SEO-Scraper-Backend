# app/middleware/auth.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from ..utils.jwt_handler import decode_token
from ..utils.supabase import get_user_by_email
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle JWT token verification for protected routes
    """
    
    async def dispatch(self, request: Request, call_next):
        # Define the protected route paths
        protected_paths = [
            "/api/users/",
            "/api/data/",
            "/api/admin/"
        ]
        
        # Public paths that don't need authentication
        public_paths = [
            "/api/auth/signin",
            "/api/auth/signup",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Check if current path needs to be protected
        path = request.url.path
        requires_auth = any(path.startswith(protected) for protected in protected_paths)
        is_public = any(path == public for public in public_paths)
        
        # Allow all OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        if not requires_auth or is_public:
            # No authentication needed, proceed to next middleware/route handler
            return await call_next(request)
        
        # Get the authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract the token
        token = auth_header.split(" ")[1]
        
        try:
            # Validate token
            payload = decode_token(token)
            
            # Extract user information
            user_id = payload.get("user_id")
            email = payload.get("sub")
            
            if not user_id or not email:
                raise JWTError("Invalid token payload")
            
            # Check if the user exists in Supabase
            user = await get_user_by_email(email)
            if not user or user["id"] != user_id:
                raise JWTError("User not found")
            
            # Attach user to request state
            request.state.user = user
            request.state.token_data = payload
            
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
