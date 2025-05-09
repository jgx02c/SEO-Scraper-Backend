from ..db.supabase import supabase, admin_supabase
from ..config import settings
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class AuthController:
    def __init__(self):
        self.supabase = supabase
        self.admin_supabase = admin_supabase

    async def get_user_by_email(self, email: str):
        """Get user by email from Supabase Auth"""
        try:
            # Get the current user from the session
            user = self.supabase.auth.get_user()
            if user and hasattr(user, 'user'):
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "roles": user.user.app_metadata.get("roles", ["user"]) if user.user.app_metadata else ["user"],
                    "hasCompletedOnboarding": user.user.user_metadata.get("hasCompletedOnboarding", False) if user.user.user_metadata else False
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    async def create_user(self, user_data: dict):
        """Create a new user in Supabase Auth"""
        try:
            # Extract data needed for signup
            email = user_data.get("email")
            password = user_data.get("password") or user_data.get("hashed_password")  # Use provided password or hash
            
            # User metadata
            user_metadata = {
                "name": user_data.get("name"),
                "hasCompletedOnboarding": user_data.get("has_completed_onboarding", False)
            }
            
            # Create the user with Supabase Auth
            try:
                # Try admin API first
                response = self.supabase.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Auto-confirm the email
                    "user_metadata": user_metadata,
                    "app_metadata": {"roles": user_data.get("roles", ["user"])}
                })
            except Exception as admin_error:
                logger.warning(f"Admin API failed, trying public API: {admin_error}")
                
                # Fallback to public API
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": user_metadata
                    }
                })
            
            if response and hasattr(response, 'user'):
                # Create profile using admin client to bypass RLS
                try:
                    profile_data = {
                        'id': response.user.id,
                        'name': user_data.get("name"),
                        'has_completed_onboarding': False,
                        'company': None,
                        'role': None,
                        'roles': ['user'],
                        'website_url': None,
                        'analysis_status': None,
                        'current_business_id': None
                    }
                    
                    # Log the profile data for debugging
                    logger.info(f"Creating user profile with data: {profile_data}")
                    
                    # Insert into user_profiles table using admin client
                    profile_response = self.admin_supabase.from_('user_profiles').insert(profile_data).execute()
                    
                    # Log the response for debugging
                    logger.info(f"Profile creation response: {profile_response}")
                    
                    if not profile_response.data:
                        logger.error("Failed to create user profile - no data returned")
                    
                except Exception as profile_error:
                    logger.error(f"Error creating user profile: {profile_error}")
                    # Continue even if profile creation fails - we can retry later
                
                # Try to sign in
                try:
                    sign_in_response = self.supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    return {
                        "id": response.user.id,
                        "email": response.user.email,
                        "roles": response.user.app_metadata.get("roles", ["user"]) if response.user.app_metadata else ["user"],
                        "token": sign_in_response.session.access_token if hasattr(sign_in_response, 'session') else None,
                        "message": "User created and signed in successfully"
                    }
                except Exception as sign_in_error:
                    if "Email not confirmed" in str(sign_in_error):
                        return {
                            "id": response.user.id,
                            "email": response.user.email,
                            "message": "Please check your email to confirm your account before signing in",
                            "requires_confirmation": True
                        }
                    raise sign_in_error
            raise Exception("Failed to create user with Supabase Auth")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def sign_in(self, email: str, password: str):
        """Sign in a user and return their session token"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response and hasattr(response, 'session'):
                # Check if email is confirmed
                if not response.user.email_confirmed_at:
                    return {
                        "message": "Please check your email to confirm your account before signing in",
                        "requires_confirmation": True,
                        "email": email
                    }
                
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "roles": response.user.app_metadata.get("roles", ["user"]) if response.user.app_metadata else ["user"],
                    "token": response.session.access_token
                }
            raise Exception("Failed to sign in with Supabase Auth")
        except Exception as e:
            if "Email not confirmed" in str(e):
                # Return a 200 OK response with a message about email confirmation
                return {
                    "message": "Please check your email to confirm your account before signing in",
                    "requires_confirmation": True,
                    "email": email
                }
            logger.error(f"Error signing in: {e}")
            raise

    async def update_user(self, user_id: str, user_data: dict):
        """Update user data in Supabase Auth"""
        try:
            # Prepare data for update
            update_data = {}
            
            # User metadata that should be updated
            if any(key in user_data for key in ["name", "hasCompletedOnboarding", "company", "role"]):
                user_metadata = {}
                if "name" in user_data:
                    user_metadata["name"] = user_data["name"]
                if "hasCompletedOnboarding" in user_data:
                    user_metadata["hasCompletedOnboarding"] = user_data["hasCompletedOnboarding"]
                if "company" in user_data:
                    user_metadata["company"] = user_data["company"]
                if "role" in user_data:
                    user_metadata["role"] = user_data["role"]
                update_data["user_metadata"] = user_metadata
            
            # App metadata for roles
            if "roles" in user_data:
                update_data["app_metadata"] = {"roles": user_data["roles"]}
            
            # Special case for password reset
            if "reset_token" in user_data:
                # Store reset token in user metadata
                if "user_metadata" not in update_data:
                    update_data["user_metadata"] = {}
                update_data["user_metadata"]["reset_token"] = user_data["reset_token"]
                update_data["user_metadata"]["reset_token_expires"] = user_data["reset_token_expires"].isoformat()
            
            # Update the user
            try:
                # Try admin API first
                response = self.supabase.auth.admin.update_user_by_id(
                    user_id, 
                    update_data
                )
            except Exception as admin_error:
                logger.warning(f"Admin API failed, trying public API: {admin_error}")
                
                # Fallback to public API - only update user metadata
                if "user_metadata" in update_data:
                    response = self.supabase.auth.update_user({
                        "data": update_data["user_metadata"]
                    })
                else:
                    raise Exception("Cannot update app metadata with public API")
            
            if response and hasattr(response, 'user'):
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "roles": response.user.app_metadata.get("roles", ["user"]) if response.user.app_metadata else ["user"]
                }
            raise Exception("Failed to update user with Supabase Auth")
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise