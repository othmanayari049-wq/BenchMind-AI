from pathlib import Path

from ..models import AgentFinding, Evidence
from .base import ModelProvider


class MockProvider(ModelProvider):
    """Offline provider used by tests and deterministic demo cases."""

    name = "mock"

    async def inspect_image(
        self, image_path: Path, question: str, evidence: Evidence
    ) -> list[AgentFinding]:
        return []
