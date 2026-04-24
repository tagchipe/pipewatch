"""Pipeline health check scoring with pass/fail/degraded states."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class HealthCheckResult:
    pipeline: str
    state: str  # "healthy" | "degraded" | "unhealthy"
    total: int
    ok_count: int
    warning_count: int
    critical_count: int
    score: float  # 0.0 – 100.0

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "state": self.state,
            "total": self.total,
            "ok_count": self.ok_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "score": round(self.score, 2),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _state_from_score(score: float) -> str:
    if score >= 90.0:
        return "healthy"
    if score >= 50.0:
        return "degraded"
    return "unhealthy"


class HealthChecker:
    """Evaluate pipeline health from a collection of metrics."""

    # Weight applied to each status when computing score
    _WEIGHTS: Dict[MetricStatus, float] = {
        MetricStatus.OK: 1.0,
        MetricStatus.WARNING: 0.5,
        MetricStatus.CRITICAL: 0.0,
    }

    def check(self, pipeline: str, metrics: List[PipelineMetric]) -> Optional[HealthCheckResult]:
        """Return a HealthCheckResult for *pipeline* using *metrics*.

        Returns None when *metrics* is empty.
        """
        relevant = [m for m in metrics if m.pipeline == pipeline]
        if not relevant:
            return None

        ok = sum(1 for m in relevant if m.status == MetricStatus.OK)
        warn = sum(1 for m in relevant if m.status == MetricStatus.WARNING)
        crit = sum(1 for m in relevant if m.status == MetricStatus.CRITICAL)
        total = len(relevant)

        weighted_sum = sum(self._WEIGHTS.get(m.status, 0.0) for m in relevant)
        score = (weighted_sum / total) * 100.0

        return HealthCheckResult(
            pipeline=pipeline,
            state=_state_from_score(score),
            total=total,
            ok_count=ok,
            warning_count=warn,
            critical_count=crit,
            score=score,
        )

    def check_all(self, metrics: List[PipelineMetric]) -> List[HealthCheckResult]:
        """Return results for every distinct pipeline present in *metrics*."""
        pipelines = dict.fromkeys(m.pipeline for m in metrics)
        return [r for p in pipelines if (r := self.check(p, metrics)) is not None]
