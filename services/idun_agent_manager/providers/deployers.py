from __future__ import annotations

import os
from typing import Protocol

import docker  # type: ignore[import-not-found]

from services.idun_agent_manager.domain.schemas import DeploymentConfig, DeploymentType


class DeploymentProvider(Protocol):
    def deploy(self, image: str, name: str, config: DeploymentConfig) -> tuple[str, str]: ...
    def delete(self, deploy_ref: str, config: DeploymentConfig) -> None: ...


class LocalDockerDeployer:
    def __init__(self) -> None:
        self.client = docker.from_env()

    def deploy(self, image: str, name: str, config: DeploymentConfig) -> tuple[str, str]:
        network = config.docker_network or os.getenv("IDUN_MANAGER_DOCKER_NETWORK", "idun_network")
        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{name}.rule": f"PathPrefix(`/api/v1/agents/{name}`)",
            f"traefik.http.services.{name}.loadbalancer.server.port": "8000",
        }

        # Ensure previous container with same name is not running
        try:
            existing = self.client.containers.get(name)
            existing.remove(force=True)
        except Exception:
            pass

        container = self.client.containers.run(
            image=image,
            name=name,
            detach=True,
            network=network,
            labels=labels,
        )
        endpoint = f"http://localhost/api/v1/agents/{name}"
        return endpoint, str(container.id)

    def delete(self, deploy_ref: str, config: DeploymentConfig) -> None:
        try:
            container = self.client.containers.get(deploy_ref)
            container.remove(force=True)
        except Exception:
            return


def get_deployer(config: DeploymentConfig) -> DeploymentProvider:
    if config.type == DeploymentType.local:
        return LocalDockerDeployer()
    raise NotImplementedError(f"Unknown deployment type: {config.type}")
