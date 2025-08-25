from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.idun_agent_manager.domain.schemas import (
    DeploymentInfo,
    ManagedAgentCreate,
    ManagedAgentUpdate,
    VersionInfo,
)
from services.idun_agent_manager.domain.schemas import (
    ManagedAgent as ManagedAgentSchema,
)
from services.idun_agent_manager.services.agent_service import (
    create_managed_agent,
    deploy_new_version,
    list_versions,
    rollback_to_version,
)
from services.idun_agent_manager.storage.database import get_session
from services.idun_agent_manager.storage.models import Deployment, ManagedAgent

router = APIRouter()


@router.post("/", response_model=ManagedAgentSchema, status_code=status.HTTP_201_CREATED)
def create_agent(payload: ManagedAgentCreate, session: Session = Depends(get_session)):
    db_agent = create_managed_agent(session, payload)
    return _to_schema(db_agent)


@router.get("/", response_model=list[ManagedAgentSchema])
def list_agents(session: Session = Depends(get_session)):
    rows = session.query(ManagedAgent).all()
    return [_to_schema(a) for a in rows]


@router.post("/{agent_id}/deploy", response_model=VersionInfo)
def deploy_agent(agent_id: str, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    version, _ = deploy_new_version(session, db_agent)
    return _to_version_info(version)


@router.get("/{agent_id}/versions", response_model=list[VersionInfo])
def get_versions(agent_id: str, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    versions = list_versions(session, agent_id)
    return [_to_version_info(v) for v in versions]


@router.post("/{agent_id}/rollback/{version}", response_model=VersionInfo)
def rollback(agent_id: str, version: int, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    v, _ = rollback_to_version(session, agent_id, version)
    return _to_version_info(v)


@router.get("/{agent_id}", response_model=ManagedAgentSchema)
def get_agent(agent_id: str, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _to_schema(db_agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: str, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    session.delete(db_agent)
    session.commit()
    return


@router.patch("/{agent_id}", response_model=ManagedAgentSchema)
def update_agent(agent_id: str, payload: ManagedAgentUpdate, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if payload.name is not None:
        db_agent.name = payload.name
    if payload.description is not None:
        db_agent.description = payload.description
    if payload.engine is not None:
        db_agent.engine_config = payload.engine.config
    if payload.retrieval is not None:
        db_agent.retriever_config = payload.retrieval.model_dump()
    if payload.deployment is not None:
        db_agent.deployment_config = payload.deployment.model_dump()
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    return _to_schema(db_agent)


@router.get("/{agent_id}/deployments", response_model=list[DeploymentInfo])
def list_deployments(agent_id: str, session: Session = Depends(get_session)):
    db_agent = session.get(ManagedAgent, agent_id)
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    rows = session.query(Deployment).filter(Deployment.agent_id == agent_id).all()
    return [
        DeploymentInfo(
            id=d.id,
            version_id=d.version_id,
            target=d.target,
            endpoint_url=d.endpoint_url,
            traefik_router=d.traefik_router,
            status=d.status,
        )
        for d in rows
    ]


def _to_schema(db: ManagedAgent) -> ManagedAgentSchema:
    from services.idun_agent_manager.domain.schemas import (
        DeploymentConfig,
        EngineConfig,
        RetrievalConfig,
    )

    return ManagedAgentSchema(
        id=db.id,
        name=db.name,
        description=db.description,
        engine=EngineConfig(config=db.engine_config),
        retrieval=RetrievalConfig.model_validate(db.retriever_config),
        deployment=DeploymentConfig.model_validate(db.deployment_config),
    )


def _to_version_info(v) -> VersionInfo:
    return VersionInfo(
        id=v.id,
        version=v.version,
        artifact_uri=v.artifact_uri,
        image_tag=v.image_tag,
        deploy_target=v.deploy_target,
        deploy_ref=v.deploy_ref,
        status=v.status,
    )
