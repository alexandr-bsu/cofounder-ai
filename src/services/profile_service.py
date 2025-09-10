import asyncio
from src.config.settings import settings
from supabase import acreate_client, AClient
from src.schemas import Profile
from typing import Optional
from src.utils import AsyncMixin


class ProfileService(AsyncMixin):
    async def __ainit__(self):
        self.supabase: AClient = await acreate_client(
            settings.supabase.supabase_url, settings.supabase.supabase_service_key)

    async def add_profile(self, form_data: Profile):
        result = await self.supabase.table('cofounder_profiles').insert(form_data.model_dump()).execute()
        return result


