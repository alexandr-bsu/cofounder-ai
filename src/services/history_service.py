from src.config.settings import settings
from supabase import acreate_client, AClient
from src.schemas import Message, ConversationHistoryMessage
from typing import Optional
from src.utils import AsyncMixin
import re

class HistoryService(AsyncMixin):
    async def __ainit__(self):
        self.supabase: AClient = await acreate_client(
            settings.supabase.supabase_url, settings.supabase.supabase_service_key)

    async def get_history(self, profile_id: str, init_topic:Optional[str] = None) -> list[Message]:
        """
        param: init_topic:str - При инициализации диалога удаляет из истории все предыдущие сообщения по теме 
        """

        if init_topic is not None:
           init_topic = re.sub(r'\s*\([^)]*\)', '', init_topic).strip()

        response = await self.supabase.rpc('get_latest_conversations_by_topic', {
            'p_profile_id': profile_id
        }).execute()

        response.data = list(filter(lambda messagge: messagge['topic'] != init_topic, response.data))
        return response

    async def get_instructions(self, topic: str):
        topic =  re.sub(r'\s*\([^)]*\)', '', topic).strip()
        response = await self.supabase.table('cofounder_system_prompts').select(
            '*').eq('topic', topic).execute()
        return response.data[0] if len(response.data) else []


    async def add_message_to_conversation_history(self, message: ConversationHistoryMessage):
        message_dict = message.model_dump()
        message_dict['topic'] = re.sub(r'\s*\([^)]*\)', '', message_dict['topic']).strip()
        
        result = await self.supabase.table('cofounder_conversation_history').insert(message_dict).execute()
        return result
