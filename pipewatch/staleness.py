"""Staleness checker — flags pipelines whose last checkpoint exceeds a max age."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from pipewatch.checkpoint import CheckpointStore, CheckpointEntry


@dataclass
class StalenessResult:
    pipeline: str
    age_seconds: float
    max_age_seconds: float
    is_stale: bool
    entry: Optional[CheckpointEntry]

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "age_seconds": round(self.age_seconds, 2),
            "max_age_seconds": self.max_age_seconds,
            "is_stale": self.is_stale,
        }


class StalenessChecker:
    def __init__(self, store: CheckpointStore):
        self._store = store
        self._rules: dict[str, float] = {}

    def register(self, pipeline: str, max_age_seconds: float) -> None:
        self._rules[pipeline] = max_age_seconds

    def check(self, pipeline: str) -> StalenessResult:
        max_age = self._rules.get(pipeline, float("inf"))
        entry = self._store.get(pipeline)
        if entry is None:
            return StalenessResult(
                pipeline=pipeline,
                age_seconds=float("inf"),
                max_age_seconds=max_age,
                is_stale=True,
                entry=None,
            )
        age = entry.age_seconds()
        return StalenessResult(
            pipeline=pipeline,
            age_seconds=age,
            max_age_seconds=max_age,
            is_stale=age > max_age,
            entry=entry,
        )

    def check_all(self) -> list[StalenessResult]:
        return [self.check(p) for p in self._rules]

    def stale_pipelines(self) -> list[StalenessResult]:
        return [r for r in self.check_all() if r.is_stale]
