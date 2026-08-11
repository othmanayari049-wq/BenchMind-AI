from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from benchmind.evidence import classify_file
from benchmind.models import EngineeringCase, Evidence
from benchmind.orchestrator import BenchMindOrchestrator
from benchmind.providers.mock import MockProvider


@dataclass
class Result:
    case_id: str
    root_cause_match: bool
    evidence_match: bool
    test_match: bool


async def evaluate_case(case_path: Path) -> Result:
    spec = json.loads(case_path.read_text(encoding="utf-8"))
    case = EngineeringCase(question=spec["question"])
    for relative in spec["files"]:
        path = (case_path.parent / relative).resolve()
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        case.evidence.append(Evidence(
            filename=path.name,
            kind=classify_file(path.name),
            size_bytes=len(data),
            text=text,
            stored_path=str(path),
        ))
    report = await BenchMindOrchestrator(MockProvider()).analyze(case)
    primary = report.diagnosis.primary
    title = primary.title if primary else ""
    used = {ref.label for ref in report.evidence_used}
    test_names = {test.name for test in report.diagnosis.tests}
    return Result(
        case_id=spec["id"],
        root_cause_match=spec["expected_root_cause_contains"].lower() in title.lower(),
        evidence_match=set(spec["expected_evidence"]).issubset(used),
        test_match=any(spec["expected_test_contains"].lower() in name.lower() for name in test_names),
    )


async def main_async(root: Path) -> int:
    paths = sorted(root.glob("*/case.json"))
    results = [await evaluate_case(path) for path in paths]
    payload = {
        "cases": [result.__dict__ for result in results],
        "summary": {
            "case_count": len(results),
            "root_cause_passes": sum(result.root_cause_match for result in results),
            "evidence_passes": sum(result.evidence_match for result in results),
            "test_plan_passes": sum(result.test_match for result in results),
        },
        "note": "These are deterministic fixture checks, not a claim of real-world diagnostic accuracy."
    }
    print(json.dumps(payload, indent=2))
    return 0 if all(r.root_cause_match and r.evidence_match and r.test_match for r in results) else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path(__file__).parent / "cases")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args.cases)))


if __name__ == "__main__":
    main()
