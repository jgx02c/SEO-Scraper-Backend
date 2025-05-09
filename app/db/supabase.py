from supabase import create_client, Client
from ..config import settings
import logging
import os
import importlib
import sys

logger = logging.getLogger(__name__)

# Monkey patch the gotrue SyncClient to handle proxy correctly
try:
    # First, import the problematic module
    from gotrue._sync.gotrue_base_api import SyncClient
    from httpx import Client as HTTPXClient
    
    # Store the original __init__ method
    original_init = SyncClient.__init__
    
    # Define a patched init method that filters out the 'proxy' keyword
    def patched_init(self, *args, **kwargs):
        # Remove the 'proxy' keyword if it exists
        if 'proxy' in kwargs:
            del kwargs['proxy']
        # Call the original init with the cleaned kwargs
        original_init(self, *args, **kwargs)
    
    # Replace the original __init__ with our patched version
    SyncClient.__init__ = patched_init
    
    logger.info("Successfully patched SyncClient.__init__ to handle proxy correctly")
except ImportError:
    logger.warning("Could not patch SyncClient, module not found")
except Exception as e:
    logger.error(f"Error patching SyncClient: {e}")

# Temporarily unset HTTP_PROXY environment variables that might be causing issues
http_proxy = os.environ.pop('http_proxy', None)
https_proxy = os.environ.pop('https_proxy', None)
HTTP_PROXY = os.environ.pop('HTTP_PROXY', None)
HTTPS_PROXY = os.environ.pop('HTTPS_PROXY', None)

# Initialize Supabase clients
try:
    # Log the configuration (without exposing sensitive data)
    logger.info(f"Initializing Supabase clients with URL: {settings.SUPABASE_URL}")
    
    # Debug log the key lengths and first few characters
    anon_key = settings.SUPABASE_KEY
    service_key = settings.SUPABASE_SERVICE_KEY
    logger.info(f"Supabase anon key length: {len(anon_key)}")
    logger.info(f"Supabase service key length: {len(service_key)}")
    
    # Initialize with the anon key for regular operations
    supabase: Client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=anon_key
    )
    
    # Initialize with the service role key for admin operations
    admin_supabase: Client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=service_key
    )
    
    logger.info("Supabase clients initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Supabase clients: {str(e)}")
    raise
finally:
    # Restore proxy environment variables
    if http_proxy:
        os.environ['http_proxy'] = http_proxy
    if https_proxy:
        os.environ['https_proxy'] = https_proxy
    if HTTP_PROXY:
        os.environ['HTTP_PROXY'] = HTTP_PROXY
    if HTTPS_PROXY:
        os.environ['HTTPS_PROXY'] = HTTPS_PROXY