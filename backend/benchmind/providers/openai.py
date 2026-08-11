from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import AsyncOpenAI

from ..models import AgentFinding, ClaimType, Evidence, EvidenceReference
from .base import ModelProvider, ProviderUnavailable


class OpenAIProvider(ModelProvider):
    name = "openai"

    def __init__(self, api_key: str | None, model: str, timeout: float) -> None:
        if not api_key:
            raise ProviderUnavailable("OPENAI_API_KEY is not configured")
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model

    async def inspect_image(
        self, image_path: Path, question: str, evidence: Evidence
    ) -> list[AgentFinding]:
        raw = image_path.read_bytes()
        media_type = evidence.media_type or "image/jpeg"
        data_url = f"data:{media_type};base64,{base64.b64encode(raw).decode('ascii')}"
        prompt = (
            "Inspect this engineering hardware/schematic image. Report only visible observations; "
            "do not invent hidden connections or component values. Return a JSON array of objects with "
            "keys statement, confidence (0..1), and tags. If uncertain, lower confidence or return []. "
            f"User question: {question}"
        )
        try:
            response = await self.client.responses.create(
                model=self.model,
                reasoning={"effort": "low"},
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": data_url, "detail": "high"},
                        ],
                    }
                ],
            )
            data = json.loads(response.output_text)
        except Exception as exc:
            raise ProviderUnavailable(f"OpenAI image analysis failed: {exc}") from exc

        findings: list[AgentFinding] = []
        if not isinstance(data, list):
            return findings
        ref = EvidenceReference(evidence_id=evidence.id, label=evidence.filename)
        for item in data:
            if not isinstance(item, dict) or not item.get("statement"):
                continue
            findings.append(
                AgentFinding(
                    agent="hardware_vision",
                    claim_type=ClaimType.OBSERVATION,
                    statement=str(item["statement"]),
                    confidence=float(item.get("confidence", 0.5)),
                    evidence=[ref],
                    tags=[str(tag) for tag in item.get("tags", [])][:8],
                )
            )
        return findings
