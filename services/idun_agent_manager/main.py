from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.idun_agent_manager.settings import Settings
from services.idun_agent_manager.storage.database import (
    create_all_tables,
    init_engine_and_session,
)
from services.idun_agent_manager.web.api import api_router

settings = Settings()  # loads from env


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB engine and create tables
    init_engine_and_session(settings.database_url)
    create_all_tables()
    yield


app = FastAPI(
    title="Idun Agent Manager",
    description="Service to retrieve, build, deploy and manage agents",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Idun Agent Manager running"}
