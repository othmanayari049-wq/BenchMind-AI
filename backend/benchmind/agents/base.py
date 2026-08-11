from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import AgentFinding, EngineeringCase


class SpecialistAgent(ABC):
    name: str

    @abstractmethod
    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        pass
