from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .evidence import save_upload
from .factory import build_provider
from .logging import configure_logging
from .models import EngineeringCase, EngineeringReport
from .orchestrator import BenchMindOrchestrator
from .providers import ProviderUnavailable
from .storage import CaseStore

configure_logging()
settings = get_settings()
store = CaseStore(settings.data_dir)

try:
    provider = build_provider(settings)
    provider_error: str | None = None
except ProviderUnavailable as exc:
    provider_error = str(exc)
    from .providers.mock import MockProvider

    provider = MockProvider()

orchestrator = BenchMindOrchestrator(provider, settings.max_parallel_agents)
app = FastAPI(
    title="BenchMind AI API",
    version="0.1.0",
    description="Evidence-grounded engineering diagnosis API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str | bool | None]:
    return {
        "status": "ok",
        "provider": provider.name,
        "provider_fallback": provider_error is not None,
        "provider_error": provider_error,
    }


@app.get("/api/v1/capabilities")
async def capabilities() -> dict[str, object]:
    return {
        "v1": {
            "inputs": ["text", "images", "PDF", "code", "logs", "CSV telemetry", "config"],
            "agents": [
                "supervisor",
                "hardware_vision",
                "firmware",
                "datasheet",
                "telemetry",
                "engineering_tools",
                "diagnosis",
                "verifier",
                "reporter",
            ],
            "model_provider": provider.name,
            "deterministic_tools": True,
            "rag": "local provenance-aware lexical retrieval",
            "sandbox_execution": False,
        },
        "planned": [
            "isolated code execution",
            "serial integration",
            "compiler adapters",
            "ROS",
            "live telemetry",
            "voice",
            "STM32/Raspberry Pi",
            "HDL tooling",
        ],
    }


@app.post("/api/v1/analyze", response_model=EngineeringReport)
async def analyze(
    question: Annotated[str, Form(min_length=3, max_length=4000)],
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> EngineeringReport:
    uploads = files or []
    if len(uploads) > settings.max_files_per_case:
        raise HTTPException(
            status_code=413,
            detail=f"At most {settings.max_files_per_case} files are allowed per case",
        )

    case = EngineeringCase(question=question)
    case_dir = settings.data_dir / "uploads" / case.id
    for upload in uploads:
        case.evidence.append(await save_upload(upload, case_dir, settings))

    report = await orchestrator.analyze(case)
    case.report = report
    store.put(case)
    return report


@app.get("/api/v1/cases/{case_id}", response_model=EngineeringCase)
async def get_case(case_id: str) -> EngineeringCase:
    case = store.get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.post("/api/v1/demo/{demo_name}", response_model=EngineeringReport)
async def run_demo(demo_name: str) -> EngineeringReport:
    root = Path(__file__).resolve().parents[2]
    demo_dir = root / "examples" / demo_name
    if not demo_dir.is_dir():
        raise HTTPException(status_code=404, detail="Demo not found")

    question_path = demo_dir / "question.txt"
    if not question_path.exists():
        raise HTTPException(status_code=500, detail="Demo is missing question.txt")
    case = EngineeringCase(question=question_path.read_text(encoding="utf-8").strip())
    from .evidence import classify_file
    from .models import Evidence

    for path in sorted(demo_dir.iterdir()):
        if path.name == "question.txt" or not path.is_file():
            continue
        data = path.read_bytes()
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
    report = await orchestrator.analyze(case)
    case.report = report
    store.put(case)
    return report
