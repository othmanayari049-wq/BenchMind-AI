from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import AgentFinding, Evidence


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def inspect_image(
        self, image_path: Path, question: str, evidence: Evidence
    ) -> list[AgentFinding]:
        """Return grounded observations from one engineering image."""


class ProviderUnavailable(RuntimeError):
    pass
