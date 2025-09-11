import asyncio
from fastapi import APIRouter, BackgroundTasks
from src.services.profile_service import ProfileService
from src.schemas import Profile, Tracker, Transition

router = APIRouter(prefix='/web')


async def add_profile_background(form_data: Profile):
    ps = await ProfileService()
    await ps.add_profile(form_data)

async def track_background(track_data: Tracker):
    ps = await ProfileService()
    await ps.track(track_data)

async def register_transition_background(transition_data: Transition):
    ps = await ProfileService()
    await ps.register_transition(transition_data)

@router.post('/addProfile', status_code=201)
async def add_profile(form_data: Profile, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_profile_background, form_data)
    return {"success": True}

@router.put('/track', status_code=201)
async def track(track_data: Tracker, background_tasks: BackgroundTasks):
    background_tasks.add_task(track_background, track_data)
    return {"success": True}

@router.post('/registerTransition', status_code=201)
async def registerTransition(transition_data: Transition, background_tasks: BackgroundTasks):
    background_tasks.add_task(register_transition_background, transition_data)
    return {"success": True}