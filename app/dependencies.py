# app/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from .database import db
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

async def get_current_user(request: Request):
    """
    Get the current authenticated user from request state
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        dict: User document from database
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return request.state.user

async def require_role(request: Request, required_roles: List[str]):
    """
    Check if the current user has the required role
    
    Args:
        request (Request): FastAPI request object
        required_roles (List[str]): List of roles required to access the resource
        
    Returns:
        dict: User document from database
        
    Raises:
        HTTPException: If user doesn't have required roles
    """
    user = await get_current_user(request)
    
    user_roles = user.get("roles", [])
    
    # Check if user has any of the required roles
    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return user

# Role-specific dependency functions
async def require_admin(request: Request):
    """Require admin role to access this resource"""
    return await require_role(request, ["admin"])

async def require_data_access(request: Request):
    """Require data_access role to access this resource"""
    return await require_role(request, ["data_access", "admin"])