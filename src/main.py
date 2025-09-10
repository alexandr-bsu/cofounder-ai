
from fastapi import FastAPI
from src.routers import ai, profile


app = FastAPI()
app.include_router(ai.router)
app.include_router(profile.router)


