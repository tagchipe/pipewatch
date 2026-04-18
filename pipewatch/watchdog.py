"""Watchdog: detect pipelines that have stopped reporting metrics."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pipewatch.metrics import PipelineMetric


@dataclass
class WatchdogResult:
    pipeline: str
    last_seen: Optional[datetime]
    timeout_seconds: float
    is_dead: bool

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "timeout_seconds": self.timeout_seconds,
            "is_dead": self.is_dead,
        }


class Watchdog:
    """Tracks last-seen times for pipelines and flags dead ones."""

    DEFAULT_TIMEOUT = 300.0  # 5 minutes

    def __init__(self) -> None:
        self._last_seen: Dict[str, datetime] = {}
        self._timeouts: Dict[str, float] = {}

    def register(self, pipeline: str, timeout_seconds: float = DEFAULT_TIMEOUT) -> None:
        self._timeouts[pipeline] = timeout_seconds

    def record(self, metric: PipelineMetric) -> None:
        self._last_seen[metric.pipeline] = datetime.utcnow()

    def check(self, pipeline: str) -> WatchdogResult:
        timeout = self._timeouts.get(pipeline, self.DEFAULT_TIMEOUT)
        last_seen = self._last_seen.get(pipeline)
        if last_seen is None:
            is_dead = True
        else:
            is_dead = (datetime.utcnow() - last_seen).total_seconds() > timeout
        return WatchdogResult(
            pipeline=pipeline,
            last_seen=last_seen,
            timeout_seconds=timeout,
            is_dead=is_dead,
        )

    def check_all(self) -> List[WatchdogResult]:
        return [self.check(p) for p in self._timeouts]

    def dead_pipelines(self) -> List[str]:
        return [r.pipeline for r in self.check_all() if r.is_dead]
