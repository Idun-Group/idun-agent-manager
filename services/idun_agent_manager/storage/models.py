from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.idun_agent_manager.storage.database import Base


class ManagedAgent(Base):
    __tablename__ = "managed_agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configurations stored as JSON blobs for MVP
    engine_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    retriever_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    deployment_config: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    versions: Mapped[list[AgentVersion]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class AgentVersion(Base):
    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("managed_agents.id"), index=True)

    # Semantic or numeric version, MVP: monotonic integer
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Artifact and deployment state
    artifact_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    image_tag: Mapped[str] = mapped_column(String(256), nullable=False)
    deploy_target: Mapped[str] = mapped_column(String(64), nullable=False)  # local|gcp|k8s
    deploy_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)  # container id, service name
    status: Mapped[str] = mapped_column(String(64), default="created")  # created|deployed|failed|rolled_back
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agent: Mapped[ManagedAgent] = relationship(back_populates="versions")


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("managed_agents.id"), index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("agent_versions.id"), index=True)

    target: Mapped[str] = mapped_column(String(64))
    endpoint_url: Mapped[str] = mapped_column(String(512))
    traefik_router: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="running")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
