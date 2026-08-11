from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EvidenceKind(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    CODE = "code"
    LOG = "log"
    TELEMETRY = "telemetry"
    CONFIG = "config"
    SCHEMATIC = "schematic"
    UNKNOWN = "unknown"


class ClaimType(StrEnum):
    OBSERVATION = "observation"
    FACT = "fact"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    RECOMMENDATION = "recommendation"


class EvidenceReference(BaseModel):
    evidence_id: str
    label: str
    page: int | None = None
    section: str | None = None
    excerpt: str | None = None


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    kind: EvidenceKind
    media_type: str | None = None
    size_bytes: int = 0
    text: str | None = None
    stored_path: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class AgentFinding(BaseModel):
    agent: str
    claim_type: ClaimType
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceReference] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    title: str
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[EvidenceReference] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceReference] = Field(default_factory=list)
    unresolved_uncertainty: list[str] = Field(default_factory=list)


class DiagnosticTest(BaseModel):
    name: str
    procedure: list[str]
    expected_observation: str
    interpretation: str
    safety_notes: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    accepted: bool
    confidence_adjustment: float = Field(default=0.0, ge=-1.0, le=1.0)
    challenges: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


class Diagnosis(BaseModel):
    primary: Hypothesis | None = None
    alternatives: list[Hypothesis] = Field(default_factory=list)
    tests: list[DiagnosticTest] = Field(default_factory=list)
    proposed_fix: list[str] = Field(default_factory=list)
    safety_considerations: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    agent: str
    status: str
    duration_ms: float
    note: str | None = None


class EngineeringReport(BaseModel):
    case_id: str
    question: str
    summary: str
    diagnosis: Diagnosis
    verification: VerificationResult
    findings: list[AgentFinding]
    evidence_used: list[EvidenceReference]
    agent_trace: list[AgentTrace]
    unresolved_uncertainty: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "AI-assisted engineering guidance must be independently verified. "
        "Do not rely on BenchMind for safety-critical decisions."
    )


class EngineeringCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    question: str = Field(min_length=3, max_length=4000)
    evidence: list[Evidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    report: EngineeringReport | None = None

    @model_validator(mode="after")
    def require_input(self) -> EngineeringCase:
        if not self.question.strip() and not self.evidence:
            raise ValueError("A case requires a question or evidence")
        return self


class RoutePlan(BaseModel):
    agents: list[str]
    reasons: dict[str, str]
