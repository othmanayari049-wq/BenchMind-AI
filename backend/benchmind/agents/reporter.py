from ..models import (
    AgentFinding,
    AgentTrace,
    Diagnosis,
    EngineeringCase,
    EngineeringReport,
    EvidenceReference,
    VerificationResult,
)


class ReportAgent:
    name = "reporter"

    def build(
        self,
        case: EngineeringCase,
        findings: list[AgentFinding],
        diagnosis: Diagnosis,
        verification: VerificationResult,
        trace: list[AgentTrace],
    ) -> EngineeringReport:
        refs: dict[tuple[str, int | None, str | None], EvidenceReference] = {}
        for finding in findings:
            for item in finding.evidence:
                refs[(item.evidence_id, item.page, item.section)] = item
        if diagnosis.primary:
            for item in diagnosis.primary.supporting_evidence:
                refs[(item.evidence_id, item.page, item.section)] = item

        if diagnosis.primary is None:
            summary = "BenchMind could not support a root cause from the available evidence. More evidence is required."
        else:
            adjusted = max(0.0, min(1.0, diagnosis.primary.confidence + verification.confidence_adjustment))
            status = "supported" if verification.accepted else "not yet verified"
            summary = f"Primary hypothesis: {diagnosis.primary.title} ({status}, adjusted confidence {adjusted:.0%})."

        unresolved = list(diagnosis.primary.unresolved_uncertainty) if diagnosis.primary else []
        unresolved.extend(verification.missing_evidence)
        return EngineeringReport(
            case_id=case.id,
            question=case.question,
            summary=summary,
            diagnosis=diagnosis,
            verification=verification,
            findings=findings,
            evidence_used=list(refs.values()),
            agent_trace=trace,
            unresolved_uncertainty=list(dict.fromkeys(unresolved)),
        )
