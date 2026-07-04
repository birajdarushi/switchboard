"""cedx/audit/checkpoint.py — crash-safe per-record checkpoint (append-only JSONL).

Each completed record is flushed+fsync'd as one line. On re-run the orchestrator loads
completed records and skips them, resuming from the last completed one — no double work,
no double delivery. Backs `make probe-crash`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from cedx.contracts import Record


def _key(rec: Record) -> str:
    return f"{rec.id}:{rec.version}:{rec.status.value}"


class Checkpoint:
    def __init__(self, path: str | None):
        self.path = Path(path) if path else None
        self._done: dict[str, Record] = {}
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = Record(**json.loads(line))
                    self._done[_key(rec)] = rec

    def has(self, rec_id: str, version: int, status: str) -> Record | None:
        return self._done.get(f"{rec_id}:{version}:{status}")

    def get_by_id(self, rec_id: str, version: int) -> Record | None:
        for k, r in self._done.items():
            if r.id == rec_id and r.version == version:
                return r
        return None

    @property
    def done_records(self) -> list[Record]:
        return list(self._done.values())

    def append(self, rec: Record) -> None:
        self._done[_key(rec)] = rec
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec.model_dump(mode="json", exclude_none=True)) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def clear(self) -> None:
        if self.path and self.path.exists():
            self.path.unlink()
