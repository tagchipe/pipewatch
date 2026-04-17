"""Baseline comparison: detect deviation of metrics from established baselines."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
from pipewatch.metrics import PipelineMetric


@dataclass
class BaselineEntry:
    pipeline: str
    name: str
    expected: float
    tolerance: float = 0.1  # fractional tolerance, e.g. 0.1 = 10%

    def deviation(self, value: float) -> float:
        """Return fractional deviation from expected."""
        if self.expected == 0:
            return abs(value)
        return abs(value - self.expected) / abs(self.expected)

    def is_within(self, value: float) -> bool:
        return self.deviation(value) <= self.tolerance


@dataclass
class DeviationResult:
    metric: PipelineMetric
    expected: float
    tolerance: float
    deviation: float
    within_baseline: bool

    def to_dict(self) -> dict:
        return {
            "pipeline": self.metric.pipeline,
            "name": self.metric.name,
            "value": self.metric.value,
            "expected": self.expected,
            "tolerance": self.tolerance,
            "deviation": round(self.deviation, 4),
            "within_baseline": self.within_baseline,
        }


class BaselineChecker:
    def __init__(self) -> None:
        self._baselines: Dict[tuple, BaselineEntry] = {}

    def register(self, entry: BaselineEntry) -> None:
        self._baselines[(entry.pipeline, entry.name)] = entry

    def check(self, metric: PipelineMetric) -> Optional[DeviationResult]:
        key = (metric.pipeline, metric.name)
        entry = self._baselines.get(key)
        if entry is None:
            return None
        dev = entry.deviation(metric.value)
        return DeviationResult(
            metric=metric,
            expected=entry.expected,
            tolerance=entry.tolerance,
            deviation=dev,
            within_baseline=entry.is_within(metric.value),
        )

    def check_all(self, metrics: list[PipelineMetric]) -> list[DeviationResult]:
        results = []
        for m in metrics:
            r = self.check(m)
            if r is not None:
                results.append(r)
        return results
