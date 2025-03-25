# app/utils/jwt_handler.py
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data (Dict): Payload data to include in token
        expires_delta (Optional[timedelta]): Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token
    
    Args:
        token (str): JWT token to decode
        
    Returns:
        Dict: Decoded payload data
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT token validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        raise