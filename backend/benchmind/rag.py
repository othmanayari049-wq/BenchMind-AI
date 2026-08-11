from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .models import Evidence, EvidenceReference

TOKEN = re.compile(r"[A-Za-z0-9_+.-]+")
PAGE = re.compile(r"\[PAGE (\d+)\]")


@dataclass(frozen=True)
class Chunk:
    evidence_id: str
    label: str
    text: str
    page: int | None


class EngineeringRetriever:
    """Deterministic local V1 retrieval with provenance; embeddings can plug in later."""

    def __init__(self, evidence: list[Evidence], chunk_chars: int = 1400) -> None:
        self.chunks: list[Chunk] = []
        for item in evidence:
            if not item.text:
                continue
            self.chunks.extend(self._chunk(item, chunk_chars))

    def search(self, query: str, limit: int = 4) -> list[EvidenceReference]:
        q = set(self._tokens(query))
        if not q:
            return []
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            tokens = self._tokens(chunk.text)
            if not tokens:
                continue
            overlap = sum(1 for token in tokens if token in q)
            if overlap == 0:
                continue
            score = overlap / math.sqrt(len(tokens))
            scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            EvidenceReference(
                evidence_id=chunk.evidence_id,
                label=chunk.label,
                page=chunk.page,
                excerpt=chunk.text[:420].strip(),
            )
            for _, chunk in scored[:limit]
        ]

    def _chunk(self, evidence: Evidence, size: int) -> list[Chunk]:
        text = evidence.text or ""
        chunks: list[Chunk] = []
        current_page: int | None = None
        cursor = 0
        while cursor < len(text):
            piece = text[cursor : cursor + size]
            page_matches = list(PAGE.finditer(piece))
            if page_matches:
                current_page = int(page_matches[-1].group(1))
            chunks.append(Chunk(evidence.id, evidence.filename, piece, current_page))
            cursor += max(1, size - 180)
        return chunks

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token.lower() for token in TOKEN.findall(text)]
