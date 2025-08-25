from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class RetrievalType(str, Enum):
    local_zip = "local_zip"
    github = "github"


class DeploymentType(str, Enum):
    local = "local"
    gcp = "gcp"
    k8s = "k8s"


class RegistryType(str, Enum):
    local = "local"
    gcr = "gcr"
    ghcr = "ghcr"
    ecr = "ecr"


class EngineConfig(BaseModel):
    # Store Idun Agent Engine configuration as-is
    config: dict[str, Any]


class RetrievalConfig(BaseModel):
    type: RetrievalType
    # local zip
    zip_b64: str | None = None
    # github
    repo: str | None = None  # "owner/repo"
    ref: str | None = None  # branch/tag/sha
    path: str | None = None  # subdirectory
    token: str | None = None


class DeploymentConfig(BaseModel):
    type: DeploymentType
    # local
    docker_network: str | None = None
    # gcp
    gcp_project_id: str | None = None
    gcp_region: str | None = None
    service_name: str | None = None
    # k8s
    namespace: str | None = None


class RegistryConfig(BaseModel):
    type: RegistryType
    registry: str | None = None
    username: str | None = None
    password: str | None = None


class ManagedAgentCreate(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    engine: EngineConfig
    retrieval: RetrievalConfig
    deployment: DeploymentConfig
    registry: RegistryConfig | None = None


class ManagedAgent(BaseModel):
    id: str
    name: str
    description: str | None
    engine: EngineConfig
    retrieval: RetrievalConfig
    deployment: DeploymentConfig
    registry: RegistryConfig | None = None


class ManagedAgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    engine: EngineConfig | None = None
    retrieval: RetrievalConfig | None = None
    deployment: DeploymentConfig | None = None
    registry: RegistryConfig | None = None


class DeployRequest(BaseModel):
    version_note: str | None = None


class VersionInfo(BaseModel):
    id: int
    version: int
    artifact_uri: str
    image_tag: str
    deploy_target: str
    deploy_ref: str | None
    status: str


class DeploymentInfo(BaseModel):
    id: int
    version_id: int
    target: str
    endpoint_url: str
    traefik_router: str | None
    status: str
