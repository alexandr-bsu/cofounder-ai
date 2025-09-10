import asyncio
from src.config.settings import settings
from supabase import acreate_client, AClient
from src.schemas import Profile, Tracker, Transition
from typing import Optional
from src.utils import AsyncMixin


class ProfileService(AsyncMixin):
    async def __ainit__(self):
        self.supabase: AClient = await acreate_client(
            settings.supabase.supabase_url, settings.supabase.supabase_service_key)

    async def add_profile(self, form_data: Profile):
        result = await self.supabase.table('cofounder_profiles').insert(form_data.model_dump()).execute()
        return result

    async def track(self, tracker_data:Tracker):
        tracker = await self.supabase.table('cofounder_analytics').upsert({**tracker_data.data.model_dump(), 'form_name': tracker_data.formName, 'current_step': tracker_data.stage}).execute()
        return tracker

    async def register_transition(self, transition_data: Transition):
        transition = await self.supabase.table('cofounder_link_relations').upsert({'id': transition_data.code, 'telegram_id': transition_data.user_id}).execute()
        return transition

