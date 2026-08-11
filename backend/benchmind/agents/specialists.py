from __future__ import annotations

from pathlib import Path

from ..models import AgentFinding, ClaimType, EngineeringCase, EvidenceKind, EvidenceReference
from ..providers.base import ModelProvider, ProviderUnavailable
from ..rag import EngineeringRetriever
from ..tools.engineering import (
    likely_error_lines,
    parse_code_pins,
    parse_i2c_addresses,
    parse_serial_baud,
    parse_wiring_pins,
)
from .base import SpecialistAgent


def ref(item, excerpt: str | None = None) -> EvidenceReference:
    return EvidenceReference(evidence_id=item.id, label=item.filename, excerpt=excerpt)


class FirmwareAgent(SpecialistAgent):
    name = "firmware"

    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        for item in case.evidence:
            if item.kind not in {EvidenceKind.CODE, EvidenceKind.CONFIG} or not item.text:
                continue
            for pin in parse_code_pins(item.text, item.filename):
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Firmware maps {pin.signal} to GPIO{pin.pin}.",
                        confidence=0.99,
                        evidence=[ref(item)],
                        tags=["pin_mapping", pin.signal, f"GPIO{pin.pin}"],
                    )
                )
            for baud in parse_serial_baud(item.text):
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Firmware/configuration specifies serial baud {baud}.",
                        confidence=0.99,
                        evidence=[ref(item)],
                        tags=["baud", str(baud)],
                    )
                )
            errors = likely_error_lines(item.text)
            for line in errors:
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Build/runtime evidence contains: {line}",
                        confidence=0.99,
                        evidence=[ref(item, line)],
                        tags=["error"],
                    )
                )
        return findings


class TelemetryAgent(SpecialistAgent):
    name = "telemetry"

    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        for item in case.evidence:
            if item.kind not in {EvidenceKind.LOG, EvidenceKind.TELEMETRY} or not item.text:
                continue
            addresses = parse_i2c_addresses(item.text)
            if addresses:
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Observed I2C address(es): {', '.join(addresses)}.",
                        confidence=0.98,
                        evidence=[ref(item)],
                        tags=["i2c", *addresses],
                    )
                )
            for baud in parse_serial_baud(item.text):
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Log/telemetry metadata specifies baud {baud}.",
                        confidence=0.98,
                        evidence=[ref(item)],
                        tags=["baud", str(baud)],
                    )
                )
            for line in likely_error_lines(item.text):
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Log contains: {line}",
                        confidence=0.99,
                        evidence=[ref(item, line)],
                        tags=["error"],
                    )
                )
        return findings


class DatasheetAgent(SpecialistAgent):
    name = "datasheet"

    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        retriever = EngineeringRetriever(
            [item for item in case.evidence if item.kind in {EvidenceKind.PDF, EvidenceKind.TEXT}]
        )
        refs = retriever.search(case.question, limit=4)
        return [
            AgentFinding(
                agent=self.name,
                claim_type=ClaimType.OBSERVATION,
                statement="Relevant engineering documentation passage retrieved for diagnosis.",
                confidence=0.85,
                evidence=[item],
                tags=["retrieval"],
            )
            for item in refs
        ]


class HardwareVisionAgent(SpecialistAgent):
    name = "hardware_vision"

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        for item in case.evidence:
            if item.kind != EvidenceKind.IMAGE or not item.stored_path:
                continue
            try:
                findings.extend(
                    await self.provider.inspect_image(Path(item.stored_path), case.question, item)
                )
            except ProviderUnavailable as exc:
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Image analysis unavailable: {exc}",
                        confidence=0.0,
                        evidence=[ref(item)],
                        tags=["provider_unavailable"],
                    )
                )
        return findings


class EngineeringToolAgent(SpecialistAgent):
    name = "engineering_tools"

    async def run(self, case: EngineeringCase) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        for item in case.evidence:
            if not item.text:
                continue
            for pin in parse_wiring_pins(item.text, item.filename):
                findings.append(
                    AgentFinding(
                        agent=self.name,
                        claim_type=ClaimType.OBSERVATION,
                        statement=f"Evidence maps {pin.signal} to GPIO{pin.pin}.",
                        confidence=0.97,
                        evidence=[ref(item)],
                        tags=["wiring_mapping", pin.signal, f"GPIO{pin.pin}"],
                    )
                )
        return findings
