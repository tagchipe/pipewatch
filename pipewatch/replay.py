"""Replay recorded metrics for testing and backfill scenarios."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from pipewatch.metrics import PipelineMetric


@dataclass
class ReplayResult:
    replayed: int
    skipped: int
    pipeline: str

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "replayed": self.replayed,
            "skipped": self.skipped,
        }


class MetricReplayer:
    """Replays a sequence of metrics through a handler, with optional filtering."""

    def __init__(self, handler: Callable[[PipelineMetric], None]) -> None:
        self._handler = handler
        self._log: List[PipelineMetric] = []

    def load(self, metrics: List[PipelineMetric]) -> None:
        """Load metrics into the replay buffer."""
        self._log.extend(metrics)

    def replay(
        self,
        pipeline: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ReplayResult:
        """Replay buffered metrics, optionally filtered by pipeline name."""
        candidates = [
            m for m in self._log
            if pipeline is None or m.pipeline == pipeline
        ]
        if limit is not None:
            candidates = candidates[:limit]

        skipped = len(self._log) - len(candidates) if pipeline else 0
        for metric in candidates:
            self._handler(metric)

        label = pipeline or "*"
        return ReplayResult(
            replayed=len(candidates),
            skipped=skipped,
            pipeline=label,
        )

    def clear(self) -> None:
        self._log.clear()

    @property
    def buffered(self) -> int:
        return len(self._log)
