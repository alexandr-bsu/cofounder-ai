
from fastapi import FastAPI
from src.routers import ai


app = FastAPI()
app.include_router(ai.router)

