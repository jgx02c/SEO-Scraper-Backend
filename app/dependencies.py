from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

async def get_current_user(request: Request):
    """Get the current user from request state (set by Supabase auth middleware)"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user 