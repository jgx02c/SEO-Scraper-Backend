from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import decode_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens for protected routes."""
    def __init__(self, app, public_endpoints: list):
        super().__init__(app)
        self.public_endpoints = public_endpoints

    async def dispatch(self, request, call_next):
        if any(request.url.path.startswith(ep) for ep in self.public_endpoints):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token required")
        
        token = token.split("Bearer ")[1]
        try:
            decode_jwt_token(token)
        except HTTPException as e:
            raise HTTPException(status_code=401, detail=str(e.detail))

        return await call_next(request)
