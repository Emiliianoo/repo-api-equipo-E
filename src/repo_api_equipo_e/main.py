from fastapi import FastAPI
from repo_api_equipo_e.routers.api import router as api_router

app = FastAPI()

app.include_router(api_router)
