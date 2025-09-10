from src.config.settings import settings
from typing import Optional
from src.utils import AsyncMixin
from httpx import AsyncClient
from src.schemas import TargetHunterRequest


class TargetHunterService(AsyncMixin):
    async def __ainit__(self):
        self.client = AsyncClient()

    async def go_to_step(self, step_id: str, uid: str, payload: dict[str, str] = None):
        request_params = TargetHunterRequest(
            step_id=step_id, uid=uid, payload=payload)

        async with AsyncClient() as client:
            response = await client.request(
                method='GET',
                url='https://smm.targethunter.ru/api/bots/addUser',
                json=request_params.model_dump()
            )
            return response

