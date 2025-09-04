from src.config.settings import settings
from supabase import create_client, Client
from src.schemas import Message


class SupabaseService:
    def __init__(self):
        self.supabase = create_client(
            settings.supabase.supabase_url, settings.supabase.supabase_service_key)

    async def get_history(self, profile_id: str) -> list[Message]:        
        response = self.supabase.rpc('get_latest_conversations_by_topic', {
            'p_profile_id': profile_id
        }).execute()

        return response
    
    async def get_instructions(self, topic: str):
        response  = self.supabase.table('cofounder_system_prompts').select('*').eq('topic', topic).execute()
        return response.data[0] if len(response.data) else []
