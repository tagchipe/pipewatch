"""Checkpoint tracking for pipeline runs — records last successful run time and metadata."""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CheckpointEntry:
    pipeline: str
    last_success: float
    metadata: dict = field(default_factory=dict)

    def age_seconds(self) -> float:
        return time.time() - self.last_success

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "last_success": self.last_success,
            "age_seconds": round(self.age_seconds(), 2),
            "metadata": self.metadata,
        }


class CheckpointStore:
    def __init__(self, path: Optional[str] = None):
        self._path = Path(path) if path else None
        self._store: dict[str, CheckpointEntry] = {}
        if self._path and self._path.exists():
            self._load()

    def record(self, pipeline: str, metadata: dict | None = None) -> CheckpointEntry:
        entry = CheckpointEntry(
            pipeline=pipeline,
            last_success=time.time(),
            metadata=metadata or {},
        )
        self._store[pipeline] = entry
        if self._path:
            self._save()
        return entry

    def get(self, pipeline: str) -> Optional[CheckpointEntry]:
        return self._store.get(pipeline)

    def all(self) -> list[CheckpointEntry]:
        return list(self._store.values())

    def _save(self) -> None:
        data = {k: v.to_dict() for k, v in self._store.items()}
        self._path.write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        for k, v in data.items():
            self._store[k] = CheckpointEntry(
                pipeline=v["pipeline"],
                last_success=v["last_success"],
                metadata=v.get("metadata", {}),
            )
