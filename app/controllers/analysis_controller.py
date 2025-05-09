from ..db.supabase import supabase
import logging

logger = logging.getLogger(__name__)

class AnalysisController:
    def __init__(self):
        self.supabase = supabase

    async def get_analysis_by_user_id(self, user_id: str):
        """Get analysis data by user ID from Supabase"""
        try:
            response = self.supabase.from_('user_profiles').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting analysis by user ID: {e}")
            return None

    async def create_analysis(self, analysis_data: dict):
        """Create new analysis data in Supabase"""
        try:
            # Update the user's profile with analysis data
            response = self.supabase.from_('user_profiles').update({
                'website_url': analysis_data.get('website_url'),
                'analysis_status': analysis_data.get('status'),
                'updated_at': analysis_data.get('updated_at')
            }).eq('id', analysis_data.get('user_id')).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise

    async def update_analysis(self, user_id: str, analysis_data: dict):
        """Update analysis data in Supabase"""
        try:
            response = self.supabase.from_('user_profiles').update({
                'website_url': analysis_data.get('website_url'),
                'analysis_status': analysis_data.get('status'),
                'updated_at': analysis_data.get('updated_at')
            }).eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating analysis: {e}")
            raise 