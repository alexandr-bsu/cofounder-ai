import asyncio
from fastapi import APIRouter, BackgroundTasks
from src.services.profile_service import ProfileService
from src.schemas import Profile

router = APIRouter(prefix='/web')


async def add_profile_background(form_data: Profile):
    ps = await ProfileService()
    await ps.add_profile(form_data)

@router.post('/addProfile', status_code=201)
async def add_profile(form_data: Profile, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_profile_background, form_data)
    return {"success": True}