from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import EngineeringCase


class CaseStore:
    """Small durable V1 store. Postgres can replace this behind the same interface later."""

    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "benchmind.db"
        data_dir.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def put(self, case: EngineeringCase) -> None:
        payload = case.model_dump_json()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO cases(id, payload) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (case.id, payload),
            )

    def get(self, case_id: str) -> EngineeringCase | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
        return EngineeringCase.model_validate_json(row[0]) if row else None
