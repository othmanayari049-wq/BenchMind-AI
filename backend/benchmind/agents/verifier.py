from ..models import Diagnosis, VerificationResult


class VerifierAgent:
    name = "verifier"

    def verify(self, diagnosis: Diagnosis) -> VerificationResult:
        if diagnosis.primary is None:
            return VerificationResult(
                accepted=False,
                challenges=["No root-cause hypothesis was produced."],
                missing_evidence=["Additional independent evidence is required before a diagnosis can be supported."],
            )

        evidence_count = len(diagnosis.primary.supporting_evidence)
        challenges: list[str] = []
        missing: list[str] = []
        adjustment = 0.0
        accepted = True

        if evidence_count < 2:
            challenges.append("Primary diagnosis currently relies on fewer than two independent evidence references.")
            missing.append("Obtain a second independent observation before treating the diagnosis as confirmed.")
            adjustment -= 0.12
        if diagnosis.primary.unresolved_uncertainty:
            challenges.extend(diagnosis.primary.unresolved_uncertainty)
            adjustment -= min(0.1, 0.03 * len(diagnosis.primary.unresolved_uncertainty))
        if diagnosis.primary.confidence + adjustment < 0.55:
            accepted = False
            challenges.append("Adjusted confidence is too low for a supported primary diagnosis.")

        return VerificationResult(
            accepted=accepted,
            confidence_adjustment=adjustment,
            challenges=challenges,
            missing_evidence=missing,
        )
