from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from services.idun_agent_manager.domain.schemas import ManagedAgentCreate
from services.idun_agent_manager.providers.deployers import get_deployer
from services.idun_agent_manager.providers.registries import LocalRegistry
from services.idun_agent_manager.providers.retrievers import get_retriever
from services.idun_agent_manager.storage.models import (
    AgentVersion,
    Deployment,
    ManagedAgent,
)


def _next_version_for_agent(session: Session, agent_id: str) -> int:
    last = session.execute(
        select(func.max(AgentVersion.version)).where(AgentVersion.agent_id == agent_id)
    ).scalar()
    return int(last or 0) + 1


def _write_engine_config(workdir: Path, engine_config: dict) -> Path:
    config_path = workdir / "config.yaml"
    import yaml  # type: ignore

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(engine_config, f, sort_keys=False)
    return config_path


def _build_local_docker_image(workdir: Path, image_tag: str) -> str:
    import docker  # type: ignore[import-not-found]

    client = docker.from_env()
    image, _ = client.images.build(path=str(workdir), tag=image_tag, rm=True)
    return image.tags[0]


def _ensure_dockerfile(workdir: Path) -> None:
    dockerfile = workdir / "Dockerfile"
    if dockerfile.exists():
        return
    # Minimal Dockerfile using idun-agent-engine runner
    dockerfile.write_text(
        "\n".join(
            [
                "FROM python:3.13-slim",
                "WORKDIR /app",
                "COPY . .",
                "RUN pip install --no-cache-dir git+https://github.com/geoffreyharrazi/idun-agent-manager#subdirectory=libs/idun_agent_engine",
                "CMD [\"python\", \"-c\", \"from idun_agent_engine.core.server_runner import run_server_from_config; run_server_from_config('config.yaml')\"]",
            ]
        ),
        encoding="utf-8",
    )


def create_managed_agent(session: Session, data: ManagedAgentCreate) -> ManagedAgent:
    agent_id = data.id or str(uuid.uuid4())
    db_agent = ManagedAgent(
        id=agent_id,
        name=data.name,
        description=data.description,
        engine_config=data.engine.config,
        retriever_config=json.loads(data.retrieval.model_dump_json()),
        deployment_config=json.loads(data.deployment.model_dump_json()),
    )
    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    return db_agent


def deploy_new_version(session: Session, db_agent: ManagedAgent) -> tuple[AgentVersion, Deployment]:
    tmpdir = Path(tempfile.mkdtemp(prefix="idun_agent_"))

    # Retrieve source
    from services.idun_agent_manager.domain.schemas import RetrievalConfig

    retrieval_cfg = RetrievalConfig.model_validate(db_agent.retriever_config)
    retriever = get_retriever(retrieval_cfg)
    source_dir = retriever.retrieve(retrieval_cfg, tmpdir)

    # Write engine config
    _write_engine_config(source_dir, db_agent.engine_config)

    # Ensure Dockerfile
    _ensure_dockerfile(source_dir)

    # Build container image
    image_tag = f"idun-agent-{db_agent.name.lower().replace(' ', '-')}:v{_next_version_for_agent(session, db_agent.id)}"
    image = _build_local_docker_image(source_dir, image_tag)

    # Push/tag to registry (MVP local)
    registry = LocalRegistry()
    artifact_uri = registry.tag_and_push(image, image_tag)

    # Record version
    version_num = _next_version_for_agent(session, db_agent.id)
    version = AgentVersion(
        agent_id=db_agent.id,
        version=version_num,
        artifact_uri=artifact_uri,
        image_tag=image_tag,
        deploy_target=db_agent.deployment_config.get("type", "local"),
        status="built",
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    # Deploy
    from services.idun_agent_manager.domain.schemas import DeploymentConfig

    deployment_cfg = DeploymentConfig.model_validate(db_agent.deployment_config)
    deployer = get_deployer(deployment_cfg)
    endpoint, deploy_ref = deployer.deploy(image=image_tag, name=f"agent-{db_agent.id}", config=deployment_cfg)

    dep = Deployment(
        agent_id=db_agent.id,
        version_id=version.id,
        target=deployment_cfg.type.value,
        endpoint_url=endpoint,
        traefik_router=f"agent-{db_agent.id}",
        status="running",
    )
    version.deploy_ref = deploy_ref
    version.status = "deployed"
    session.add(dep)
    session.add(version)
    session.commit()
    session.refresh(dep)
    session.refresh(version)
    return version, dep


def list_versions(session: Session, agent_id: str) -> list[AgentVersion]:
    from sqlalchemy import select

    rows = session.execute(
        select(AgentVersion).where(AgentVersion.agent_id == agent_id).order_by(AgentVersion.version.desc())
    ).scalars()
    return list(rows)


def rollback_to_version(session: Session, agent_id: str, version_number: int) -> tuple[AgentVersion, Deployment]:
    # Find target version
    v = session.execute(
        select(AgentVersion).where(
            (AgentVersion.agent_id == agent_id) & (AgentVersion.version == version_number)
        )
    ).scalar_one()

    # Redeploy using recorded image tag
    from services.idun_agent_manager.domain.schemas import DeploymentConfig
    from services.idun_agent_manager.storage.models import ManagedAgent

    agent = session.get(ManagedAgent, agent_id)
    if agent is None:
        raise ValueError("Agent not found")

    deployment_cfg = DeploymentConfig.model_validate(agent.deployment_config)
    deployer = get_deployer(deployment_cfg)

    endpoint, deploy_ref = deployer.deploy(image=v.image_tag, name=f"agent-{agent_id}", config=deployment_cfg)

    dep = Deployment(
        agent_id=agent_id,
        version_id=v.id,
        target=deployment_cfg.type.value,
        endpoint_url=endpoint,
        traefik_router=f"agent-{agent_id}",
        status="running",
    )
    v.deploy_ref = deploy_ref
    v.status = "deployed"
    session.add(dep)
    session.add(v)
    session.commit()
    session.refresh(dep)
    session.refresh(v)
    return v, dep
