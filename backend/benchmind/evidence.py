from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from .config import Settings
from .models import Evidence, EvidenceKind

CODE_EXTENSIONS = {".ino", ".c", ".h", ".cc", ".cpp", ".hpp", ".py", ".v", ".sv", ".vhd", ".vhdl"}
LOG_EXTENSIONS = {".log"}
TEXT_EXTENSIONS = {".txt", ".md"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
TELEMETRY_EXTENSIONS = {".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SCHEMATIC_EXTENSIONS = {".kicad_sch", ".sch"}
ALLOWED_EXTENSIONS = (
    CODE_EXTENSIONS
    | LOG_EXTENSIONS
    | TEXT_EXTENSIONS
    | CONFIG_EXTENSIONS
    | TELEMETRY_EXTENSIONS
    | IMAGE_EXTENSIONS
    | SCHEMATIC_EXTENSIONS
    | {".pdf"}
)


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not safe or safe in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return safe[:160]


def classify_file(filename: str) -> EvidenceKind:
    suffix = Path(filename).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return EvidenceKind.IMAGE
    if suffix == ".pdf":
        return EvidenceKind.PDF
    if suffix in CODE_EXTENSIONS:
        return EvidenceKind.CODE
    if suffix in LOG_EXTENSIONS:
        return EvidenceKind.LOG
    if suffix in TELEMETRY_EXTENSIONS:
        return EvidenceKind.TELEMETRY
    if suffix in CONFIG_EXTENSIONS:
        return EvidenceKind.CONFIG
    if suffix in SCHEMATIC_EXTENSIONS:
        return EvidenceKind.SCHEMATIC
    if suffix in TEXT_EXTENSIONS:
        return EvidenceKind.TEXT
    return EvidenceKind.UNKNOWN


def _extract_pdf(path: Path) -> tuple[str, dict[str, int]]:
    try:
        reader = PdfReader(str(path))
        pages: list[str] = []
        offsets: dict[str, int] = {}
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            offsets[f"page_{index}"] = len("\n".join(pages))
            pages.append(f"[PAGE {index}]\n{text}")
        return "\n\n".join(pages), offsets
    except Exception as exc:  # pypdf raises several parser-specific exceptions
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}") from exc


async def save_upload(upload: UploadFile, case_dir: Path, settings: Settings) -> Evidence:
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")
    filename = sanitize_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {suffix or 'none'}")

    data = await upload.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {settings.max_upload_bytes} byte limit"
        )

    case_dir.mkdir(parents=True, exist_ok=True)
    path = case_dir / filename
    path.write_bytes(data)
    kind = classify_file(filename)
    text: str | None = None
    metadata: dict[str, str | int | float | bool | None] = {}

    if kind == EvidenceKind.PDF:
        text, page_offsets = _extract_pdf(path)
        metadata["page_count"] = len(page_offsets)
    elif kind not in {EvidenceKind.IMAGE}:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
            metadata["decode_warnings"] = True

    return Evidence(
        filename=filename,
        kind=kind,
        media_type=upload.content_type,
        size_bytes=len(data),
        text=text,
        stored_path=str(path),
        metadata=metadata,
    )
