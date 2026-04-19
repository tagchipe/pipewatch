"""Pipeline health scorer — assigns a numeric health score to a pipeline based on its metrics."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pipewatch.metrics import PipelineMetric, MetricStatus
import json


@dataclass
class ScoredPipeline:
    pipeline: str
    score: float  # 0.0 (worst) to 100.0 (best)
    total: int
    ok: int
    warning: int
    critical: int

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "score": round(self.score, 2),
            "total": self.total,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class PipelineScorer:
    """Scores pipelines by weighting metric statuses."""

    # Weights: each status contributes this fraction to the score
    _WEIGHTS: Dict[MetricStatus, float] = {
        MetricStatus.OK: 1.0,
        MetricStatus.WARNING: 0.5,
        MetricStatus.CRITICAL: 0.0,
    }

    def score(self, metrics: List[PipelineMetric]) -> Optional[ScoredPipeline]:
        if not metrics:
            return None
        pipeline = metrics[0].pipeline
        counts = {s: 0 for s in MetricStatus}
        for m in metrics:
            counts[m.status] = counts.get(m.status, 0) + 1
        total = len(metrics)
        weighted = sum(self._WEIGHTS[s] * counts[s] for s in MetricStatus)
        score = (weighted / total) * 100.0
        return ScoredPipeline(
            pipeline=pipeline,
            score=score,
            total=total,
            ok=counts[MetricStatus.OK],
            warning=counts[MetricStatus.WARNING],
            critical=counts[MetricStatus.CRITICAL],
        )

    def score_all(self, metrics: List[PipelineMetric]) -> List[ScoredPipeline]:
        grouped: Dict[str, List[PipelineMetric]] = {}
        for m in metrics:
            grouped.setdefault(m.pipeline, []).append(m)
        results = [self.score(group) for group in grouped.values()]
        return [r for r in results if r is not None]
