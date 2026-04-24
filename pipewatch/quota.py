"""Quota enforcement: cap the number of metrics accepted per pipeline per window."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class QuotaResult:
    pipeline: str
    accepted: bool
    used: int
    limit: int
    window_seconds: int

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "accepted": self.accepted,
            "used": self.used,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
        }


@dataclass
class _QuotaState:
    limit: int
    window_seconds: int
    timestamps: list = field(default_factory=list)

    def prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def count(self, now: float) -> int:
        self.prune(now)
        return len(self.timestamps)

    def record(self, now: float) -> None:
        self.timestamps.append(now)


class QuotaManager:
    """Enforce per-pipeline metric ingestion quotas over a rolling time window."""

    def __init__(self, default_limit: int = 100, default_window: int = 60) -> None:
        self._default_limit = default_limit
        self._default_window = default_window
        self._states: Dict[str, _QuotaState] = {}

    def register(self, pipeline: str, limit: int, window_seconds: int = 60) -> None:
        self._states[pipeline] = _QuotaState(limit=limit, window_seconds=window_seconds)

    def _state(self, pipeline: str) -> _QuotaState:
        if pipeline not in self._states:
            self._states[pipeline] = _QuotaState(
                limit=self._default_limit, window_seconds=self._default_window
            )
        return self._states[pipeline]

    def check(self, metric: PipelineMetric, _now: Optional[float] = None) -> QuotaResult:
        now = _now if _now is not None else time.time()
        state = self._state(metric.pipeline)
        used = state.count(now)
        accepted = used < state.limit
        if accepted:
            state.record(now)
            used += 1
        return QuotaResult(
            pipeline=metric.pipeline,
            accepted=accepted,
            used=used,
            limit=state.limit,
            window_seconds=state.window_seconds,
        )

    def remaining(self, pipeline: str, _now: Optional[float] = None) -> int:
        now = _now if _now is not None else time.time()
        state = self._state(pipeline)
        return max(0, state.limit - state.count(now))
