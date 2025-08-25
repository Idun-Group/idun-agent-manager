from __future__ import annotations

from typing import Protocol

from services.idun_agent_manager.domain.schemas import RegistryConfig, RegistryType


class RegistryProvider(Protocol):
    def tag_and_push(self, local_image: str, target_tag: str) -> str:  # returns artifact uri
        ...


class LocalRegistry:
    def tag_and_push(self, local_image: str, target_tag: str) -> str:
        # MVP: no-op push, just return a local artifact URI
        return f"local://{target_tag}"


class GCRRegistry:
    def tag_and_push(self, local_image: str, target_tag: str) -> str:
        raise NotImplementedError("GCR push not implemented in MVP")


class GHCRRegistry:
    def tag_and_push(self, local_image: str, target_tag: str) -> str:
        raise NotImplementedError("GHCR push not implemented in MVP")


class ECRRegistry:
    def tag_and_push(self, local_image: str, target_tag: str) -> str:
        raise NotImplementedError("ECR push not implemented in MVP")


def get_registry(cfg: RegistryConfig | None) -> RegistryProvider:
    if cfg is None or cfg.type == RegistryType.local:
        return LocalRegistry()
    if cfg.type == RegistryType.gcr:
        return GCRRegistry()
    if cfg.type == RegistryType.ghcr:
        return GHCRRegistry()
    if cfg.type == RegistryType.ecr:
        return ECRRegistry()
    raise NotImplementedError(f"Unknown registry type: {cfg.type if cfg else 'None'}")
