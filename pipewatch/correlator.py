"""Metric correlation: detect when two metrics move together."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import statistics


@dataclass
class CorrelationResult:
    metric_a: str
    metric_b: str
    coefficient: float  # Pearson r, -1..1
    sample_count: int

    def to_dict(self) -> dict:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "coefficient": round(self.coefficient, 4),
            "sample_count": self.sample_count,
        }

    @property
    def is_strong(self) -> bool:
        return abs(self.coefficient) >= 0.8


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    n = len(xs)
    if n < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_a = sum((x - mx) ** 2 for x in xs) ** 0.5
    den_b = sum((y - my) ** 2 for y in ys) ** 0.5
    if den_a == 0 or den_b == 0:
        return None
    return num / (den_a * den_b)


class MetricCorrelator:
    """Accumulates metric values and computes pairwise Pearson correlation."""

    def __init__(self, max_samples: int = 100) -> None:
        self._max = max_samples
        self._series: Dict[str, List[float]] = {}

    def record(self, name: str, value: float) -> None:
        buf = self._series.setdefault(name, [])
        buf.append(value)
        if len(buf) > self._max:
            buf.pop(0)

    def correlate(self, name_a: str, name_b: str) -> Optional[CorrelationResult]:
        xs = self._series.get(name_a, [])
        ys = self._series.get(name_b, [])
        n = min(len(xs), len(ys))
        if n < 2:
            return None
        r = _pearson(xs[-n:], ys[-n:])
        if r is None:
            return None
        return CorrelationResult(name_a, name_b, r, n)

    def all_pairs(self) -> List[CorrelationResult]:
        names = list(self._series.keys())
        results = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                r = self.correlate(a, b)
                if r is not None:
                    results.append(r)
        return results
