"""Simple linear trend forecaster for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

from pipewatch.metrics import PipelineMetric


@dataclass
class ForecastResult:
    pipeline: str
    metric_name: str
    samples: int
    slope: float          # units per sample
    intercept: float
    next_value: float     # predicted value at samples+1
    horizon: int          # steps ahead used for next_value

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "samples": self.samples,
            "slope": round(self.slope, 6),
            "intercept": round(self.intercept, 6),
            "next_value": round(self.next_value, 6),
            "horizon": self.horizon,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class MetricForecaster:
    """Accumulates metric values and produces a linear forecast."""

    def __init__(self, min_samples: int = 3, horizon: int = 1) -> None:
        if min_samples < 2:
            raise ValueError("min_samples must be >= 2")
        self._min_samples = min_samples
        self._horizon = horizon
        self._data: Dict[str, List[float]] = {}

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def record(self, metric: PipelineMetric) -> None:
        key = self._key(metric)
        self._data.setdefault(key, []).append(metric.value)

    def forecast(self, metric: PipelineMetric) -> Optional[ForecastResult]:
        key = self._key(metric)
        values = self._data.get(key, [])
        n = len(values)
        if n < self._min_samples:
            return None

        xs = list(range(n))
        mean_x = sum(xs) / n
        mean_y = sum(values) / n

        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
        den = sum((x - mean_x) ** 2 for x in xs)
        slope = num / den if den != 0.0 else 0.0
        intercept = mean_y - slope * mean_x

        next_x = n - 1 + self._horizon
        next_value = intercept + slope * next_x

        return ForecastResult(
            pipeline=metric.pipeline,
            metric_name=metric.name,
            samples=n,
            slope=slope,
            intercept=intercept,
            next_value=next_value,
            horizon=self._horizon,
        )
