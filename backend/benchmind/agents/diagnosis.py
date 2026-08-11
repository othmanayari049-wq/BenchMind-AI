from __future__ import annotations

import re
from collections import defaultdict

from ..models import (
    AgentFinding,
    Diagnosis,
    DiagnosticTest,
    EngineeringCase,
    EvidenceReference,
    Hypothesis,
)
from ..tools.engineering import parse_i2c_addresses, parse_serial_baud


class DiagnosisAgent:
    name = "diagnosis"

    def synthesize(self, case: EngineeringCase, findings: list[AgentFinding]) -> Diagnosis:
        diagnosis = self._pin_mismatch(findings)
        if diagnosis.primary:
            return diagnosis
        diagnosis = self._i2c_mismatch(case)
        if diagnosis.primary:
            return diagnosis
        diagnosis = self._baud_mismatch(case)
        if diagnosis.primary:
            return diagnosis
        diagnosis = self._explicit_ground_fault(case)
        if diagnosis.primary:
            return diagnosis
        diagnosis = self._compiler_error(findings)
        if diagnosis.primary:
            return diagnosis
        return Diagnosis(
            primary=None,
            tests=[
                DiagnosticTest(
                    name="Collect additional evidence",
                    procedure=[
                        "Provide a clear wiring/schematic view or explicit pin map.",
                        "Provide firmware/configuration and the relevant runtime/build log.",
                        (
                            "Include the component datasheet when electrical limits or pin "
                            "functions are uncertain."
                        ),
                    ],
                    expected_observation=(
                        "Enough independent evidence to compare intended and observed behavior."
                    ),
                    interpretation=(
                        "BenchMind does not force a root cause when the available evidence "
                        "is insufficient."
                    ),
                )
            ],
        )

    def _pin_mismatch(self, findings: list[AgentFinding]) -> Diagnosis:
        mappings: dict[str, list[tuple[str, EvidenceReference, str]]] = defaultdict(list)
        for finding in findings:
            if "pin_mapping" not in finding.tags and "wiring_mapping" not in finding.tags:
                continue
            signal_tags = [
                tag
                for tag in finding.tags
                if tag not in {"pin_mapping", "wiring_mapping"} and not tag.startswith("GPIO")
            ]
            gpio_tags = [tag for tag in finding.tags if tag.startswith("GPIO")]
            if signal_tags and gpio_tags and finding.evidence:
                mappings[signal_tags[0]].append(
                    (gpio_tags[0], finding.evidence[0], finding.agent)
                )
        for signal, values in mappings.items():
            unique = {gpio for gpio, _, _ in values}
            if len(unique) < 2:
                continue
            refs = [ref for _, ref, _ in values]
            detail = ", ".join(f"{agent}={gpio}" for gpio, _, agent in values)
            return Diagnosis(
                primary=Hypothesis(
                    title=f"{signal} pin-definition mismatch",
                    root_cause=(
                        f"The evidence disagrees on the GPIO used for {signal}: {detail}."
                    ),
                    confidence=0.94,
                    supporting_evidence=refs,
                    unresolved_uncertainty=[
                        "A powered-off continuity/wiring check is still required."
                    ],
                ),
                tests=[
                    DiagnosticTest(
                        name="Verify pin continuity and firmware mapping",
                        procedure=[
                            "Power the circuit off.",
                            f"Trace the {signal} wire from the peripheral to the MCU pin.",
                            "Compare that physical GPIO with the firmware pin definition.",
                            (
                                "Correct one side so the physical and firmware mappings agree, "
                                "then retest."
                            ),
                        ],
                        expected_observation=(
                            "The physical GPIO and firmware GPIO should match exactly."
                        ),
                        interpretation=(
                            "If they differ, the mismatch is confirmed. If they match, "
                            "investigate an alternative hypothesis."
                        ),
                        safety_notes=["Do not move wiring on an energized circuit."],
                    )
                ],
                proposed_fix=[
                    (
                        f"Align the {signal} firmware definition and physical wiring to the "
                        "same verified GPIO."
                    )
                ],
                safety_considerations=["Disconnect power before rewiring."],
            )
        return Diagnosis()

    def _i2c_mismatch(self, case: EngineeringCase) -> Diagnosis:
        code_values: list[tuple[str, EvidenceReference]] = []
        observed_values: list[tuple[str, EvidenceReference]] = []
        for item in case.evidence:
            if not item.text:
                continue
            values = parse_i2c_addresses(item.text)
            for value in values:
                target = (
                    observed_values
                    if "scan" in item.text.lower() or "found" in item.text.lower()
                    else code_values
                )
                target.append(
                    (value, EvidenceReference(evidence_id=item.id, label=item.filename))
                )
        code_set = {v for v, _ in code_values}
        observed_set = {v for v, _ in observed_values}
        if code_set and observed_set and code_set.isdisjoint(observed_set):
            refs = [r for _, r in code_values + observed_values]
            return Diagnosis(
                primary=Hypothesis(
                    title="I2C address mismatch",
                    root_cause=(
                        f"Firmware/document evidence uses {sorted(code_set)}, while the bus "
                        f"scan observes {sorted(observed_set)}."
                    ),
                    confidence=0.96,
                    supporting_evidence=refs,
                ),
                tests=[
                    DiagnosticTest(
                        name="Confirm the device address",
                        procedure=[
                            "Run an I2C scanner on the target bus.",
                            (
                                "Compare the detected address with the address configured "
                                "in firmware."
                            ),
                        ],
                        expected_observation=(
                            f"The configured address should be one of {sorted(observed_set)}."
                        ),
                        interpretation=(
                            "A different configured address prevents communication with the "
                            "detected device."
                        ),
                    )
                ],
                proposed_fix=[
                    (
                        "Configure the driver with a verified bus address: "
                        f"one of {sorted(observed_set)}."
                    )
                ],
            )
        return Diagnosis()

    def _baud_mismatch(self, case: EngineeringCase) -> Diagnosis:
        code_baud: set[int] = set()
        other_baud: set[int] = set()
        refs: list[EvidenceReference] = []
        for item in case.evidence:
            if not item.text:
                continue
            values = set(parse_serial_baud(item.text))
            if not values:
                continue
            refs.append(EvidenceReference(evidence_id=item.id, label=item.filename))
            if "Serial.begin" in item.text:
                code_baud |= values
            if re.search(r"monitor[_ -]?baud|baud(?:rate)?\s*[:=]", item.text, re.I):
                other_baud |= values
        if code_baud and other_baud and code_baud.isdisjoint(other_baud):
            return Diagnosis(
                primary=Hypothesis(
                    title="Serial baud-rate mismatch",
                    root_cause=(
                        f"Firmware uses {sorted(code_baud)} baud while monitor/config "
                        f"evidence uses {sorted(other_baud)}."
                    ),
                    confidence=0.98,
                    supporting_evidence=refs,
                ),
                tests=[
                    DiagnosticTest(
                        name="Align serial baud rates",
                        procedure=[
                            "Read the firmware Serial.begin value.",
                            "Set the serial monitor to exactly the same baud rate.",
                            "Reset the board and inspect the output.",
                        ],
                        expected_observation=(
                            "Readable serial output after both ends use the same baud rate."
                        ),
                        interpretation="Readable output confirms the mismatch was causal.",
                    )
                ],
                proposed_fix=["Set the serial monitor and firmware to the same baud rate."],
            )
        return Diagnosis()

    def _explicit_ground_fault(self, case: EngineeringCase) -> Diagnosis:
        patterns = (
            "gnd not connected",
            "ground not connected",
            "missing common ground",
            "no common ground",
        )
        for item in case.evidence:
            lower = (item.text or "").lower()
            if any(pattern in lower for pattern in patterns):
                evidence = EvidenceReference(evidence_id=item.id, label=item.filename)
                return Diagnosis(
                    primary=Hypothesis(
                        title="Missing common ground",
                        root_cause=(
                            "The evidence explicitly indicates that the devices do not share "
                            "a common ground reference."
                        ),
                        confidence=0.97,
                        supporting_evidence=[evidence],
                    ),
                    tests=[
                        DiagnosticTest(
                            name="Verify common ground",
                            procedure=[
                                "Power the system off.",
                                (
                                    "Verify that controller and peripheral ground pins are "
                                    "electrically connected."
                                ),
                                "Restore power only after confirming the wiring.",
                            ],
                            expected_observation=(
                                "A continuous common ground connection between interacting "
                                "devices."
                            ),
                            interpretation=(
                                "A missing reference can prevent valid logic-level communication."
                            ),
                            safety_notes=["Power off before continuity testing or rewiring."],
                        )
                    ],
                    proposed_fix=[
                        (
                            "Connect communicating devices to a verified common ground when "
                            "the system design permits it."
                        )
                    ],
                    safety_considerations=[
                        (
                            "Do not bridge isolated grounds unless the system design "
                            "explicitly permits it."
                        )
                    ],
                )
        return Diagnosis()

    def _compiler_error(self, findings: list[AgentFinding]) -> Diagnosis:
        errors = [f for f in findings if "error" in f.tags and f.evidence]
        if not errors:
            return Diagnosis()
        first = errors[0]
        return Diagnosis(
            primary=Hypothesis(
                title="Compiler/runtime error reported",
                root_cause=first.statement,
                confidence=0.9,
                supporting_evidence=first.evidence,
                unresolved_uncertainty=[
                    (
                        "The exact fix depends on the full error context and surrounding "
                        "source."
                    )
                ],
            ),
            tests=[
                DiagnosticTest(
                    name="Reproduce the first error deterministically",
                    procedure=[
                        "Run the documented build command in the intended toolchain.",
                        "Fix the earliest actionable error first.",
                        "Rebuild before addressing cascaded errors.",
                    ],
                    expected_observation=(
                        "The first compiler error should disappear after its root cause "
                        "is corrected."
                    ),
                    interpretation=(
                        "Later compiler messages may be secondary effects of the first failure."
                    ),
                )
            ],
        )
