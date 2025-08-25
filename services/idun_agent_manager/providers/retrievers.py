from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path
from typing import Protocol

try:
    from git import Repo  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - lazy import fallback
    Repo = None  # type: ignore[assignment]

from services.idun_agent_manager.domain.schemas import RetrievalConfig, RetrievalType


class RetrievalProvider(Protocol):
    def retrieve(self, config: RetrievalConfig, workdir: Path) -> Path:  # returns agent dir
        ...


class LocalZipRetriever:
    def retrieve(self, config: RetrievalConfig, workdir: Path) -> Path:
        if not config.zip_b64:
            raise ValueError("zip_b64 is required for local_zip retrieval")
        data = base64.b64decode(config.zip_b64)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(workdir)
        return workdir


class GithubRetriever:
    def retrieve(self, config: RetrievalConfig, workdir: Path) -> Path:
        if not config.repo:
            raise ValueError("repo is required for github retrieval")
        ref = config.ref or "main"
        url = f"https://github.com/{config.repo}.git"
        if Repo is None:
            raise RuntimeError("GitPython not available or git not installed in container")
        Repo.clone_from(url, workdir, depth=1, branch=ref)
        subdir = workdir / (config.path or "")
        return subdir


def get_retriever(config: RetrievalConfig) -> RetrievalProvider:
    if config.type == RetrievalType.local_zip:
        return LocalZipRetriever()
    if config.type == RetrievalType.github:
        return GithubRetriever()
    raise NotImplementedError(f"Unknown retrieval type: {config.type}")
