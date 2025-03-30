from supabase import create_client, Client
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# Helper functions for Supabase operations
async def get_user_by_email(email: str):
    """Get user by email from Supabase"""
    try:
        response = supabase.table('users').select('*').eq('email', email).single().execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

async def create_user(user_data: dict):
    """Create a new user in Supabase"""
    try:
        response = supabase.table('users').insert(user_data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

async def update_user(user_id: str, user_data: dict):
    """Update user data in Supabase"""
    try:
        response = supabase.table('users').update(user_data).eq('id', user_id).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise

async def get_business_by_id(business_id: str):
    """Get business by ID from Supabase"""
    try:
        response = supabase.table('business').select('*').eq('business_id', business_id).single().execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting business by ID: {e}")
        return None

async def create_business(business_data: dict):
    """Create a new business in Supabase"""
    try:
        response = supabase.table('business').insert(business_data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating business: {e}")
        raise

async def update_business(business_id: str, business_data: dict):
    """Update business data in Supabase"""
    try:
        response = supabase.table('business').update(business_data).eq('business_id', business_id).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating business: {e}")
        raise

async def get_analysis_by_user_id(user_id: str):
    """Get analysis data by user ID from Supabase"""
    try:
        response = supabase.table('analysis').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting analysis by user ID: {e}")
        return None

async def create_analysis(analysis_data: dict):
    """Create new analysis data in Supabase"""
    try:
        response = supabase.table('analysis').insert(analysis_data).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        raise

async def update_analysis(user_id: str, analysis_data: dict):
    """Update analysis data in Supabase"""
    try:
        response = supabase.table('analysis').update(analysis_data).eq('user_id', user_id).execute()
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating analysis: {e}")
        raise 