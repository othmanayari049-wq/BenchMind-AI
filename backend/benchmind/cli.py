from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .config import get_settings
from .evidence import classify_file
from .factory import build_provider
from .models import EngineeringCase, Evidence
from .orchestrator import BenchMindOrchestrator


async def _run(question: str, paths: list[Path]) -> None:
    settings = get_settings()
    provider = build_provider(settings)
    case = EngineeringCase(question=question)
    for path in paths:
        data = path.read_bytes()
        text: str | None
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        case.evidence.append(
            Evidence(
                filename=path.name,
                kind=classify_file(path.name),
                size_bytes=len(data),
                text=text,
                stored_path=str(path),
            )
        )
    report = await BenchMindOrchestrator(provider, settings.max_parallel_agents).analyze(case)
    print(json.dumps(report.model_dump(mode="json"), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a BenchMind engineering case")
    parser.add_argument("question")
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    asyncio.run(_run(args.question, args.files))


if __name__ == "__main__":
    main()
