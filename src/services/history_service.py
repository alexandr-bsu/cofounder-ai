from src.config.settings import settings
from supabase import acreate_client, AClient
from src.schemas import Message
from typing import Optional

class HistoryService:
    def __init__(self):
        self.supabase: AClient = acreate_client(
            settings.supabase.supabase_url, settings.supabase.supabase_service_key)

    async def get_history(self, profile_id: str, init_topic:Optional[str] = None) -> list[Message]:
        """
        param: init_topic:str - При инициализации диалога удаляет из истории все предыдущие сообщения по теме 
        """

        response = await self.supabase.rpc('get_latest_conversations_by_topic', {
            'p_profile_id': profile_id
        }).execute()

        response.data = list(filter(lambda messagge: messagge['topic'] != init_topic, response.data))
        return response

    async def get_instructions(self, topic: str):
        response = await self.supabase.table('cofounder_system_prompts').select(
            '*').eq('topic', topic).execute()
        return response.data[0] if len(response.data) else []

