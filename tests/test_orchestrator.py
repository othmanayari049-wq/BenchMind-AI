from pathlib import Path

import pytest

from benchmind.evidence import classify_file
from benchmind.models import EngineeringCase, Evidence
from benchmind.orchestrator import BenchMindOrchestrator
from benchmind.providers.mock import MockProvider

ROOT = Path(__file__).resolve().parents[1]


def load_case(name: str) -> EngineeringCase:
    directory = ROOT / "examples" / name
    case = EngineeringCase(
        question=(directory / "question.txt").read_text(encoding="utf-8").strip()
    )
    for path in directory.iterdir():
        if path.name == "question.txt":
            continue
        data = path.read_bytes()
        case.evidence.append(
            Evidence(
                filename=path.name,
                kind=classify_file(path.name),
                size_bytes=len(data),
                text=data.decode("utf-8"),
                stored_path=str(path),
            )
        )
    return case


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("esp32_wrong_gpio", "ECHO pin-definition mismatch"),
        ("baud_mismatch", "Serial baud-rate mismatch"),
        ("i2c_address", "I2C address mismatch"),
        ("missing_ground", "Missing common ground"),
    ],
)
async def test_demo_root_causes(name: str, expected: str) -> None:
    report = await BenchMindOrchestrator(MockProvider()).analyze(load_case(name))
    assert report.diagnosis.primary is not None
    assert report.diagnosis.primary.title == expected


async def test_insufficient_evidence_is_explicit() -> None:
    case = EngineeringCase(question="Why does my sensor fail?")
    report = await BenchMindOrchestrator(MockProvider()).analyze(case)
    assert report.diagnosis.primary is None
    assert report.verification.accepted is False
    assert report.unresolved_uncertainty
