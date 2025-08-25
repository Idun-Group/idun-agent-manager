from fastapi import APIRouter

from services.idun_agent_manager.web.endpoints import agents

api_router = APIRouter()
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
