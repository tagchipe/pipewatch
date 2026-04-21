"""Metric sampler: probabilistic and interval-based sampling for high-volume pipelines."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class SampleResult:
    metric: PipelineMetric
    sampled: bool
    reason: str  # "rate", "interval", "always"

    def to_dict(self) -> dict:
        return {
            "metric": self.metric.to_dict(),
            "sampled": self.sampled,
            "reason": self.reason,
        }


@dataclass
class _SamplerState:
    last_sampled_at: float = 0.0
    total_seen: int = 0
    total_sampled: int = 0


class MetricSampler:
    """Decides whether a given metric should be processed based on sampling rules.

    Two strategies are supported per pipeline:
      - ``rate``: accept each metric with probability *sample_rate* (0.0–1.0).
      - ``interval``: accept at most one metric per *interval_seconds* window.

    Pipelines without an explicit rule are always accepted.
    """

    def __init__(self) -> None:
        self._rate_rules: dict[str, float] = {}
        self._interval_rules: dict[str, float] = {}
        self._state: dict[str, _SamplerState] = {}

    def register_rate(self, pipeline: str, sample_rate: float) -> None:
        """Register a probabilistic sampling rate for *pipeline* (0.0–1.0)."""
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")
        self._rate_rules[pipeline] = sample_rate

    def register_interval(self, pipeline: str, interval_seconds: float) -> None:
        """Register a minimum interval between accepted samples for *pipeline*."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._interval_rules[pipeline] = interval_seconds

    def _get_state(self, pipeline: str) -> _SamplerState:
        if pipeline not in self._state:
            self._state[pipeline] = _SamplerState()
        return self._state[pipeline]

    def check(self, metric: PipelineMetric) -> SampleResult:
        """Evaluate whether *metric* should be sampled."""
        pipeline = metric.pipeline
        state = self._get_state(pipeline)
        state.total_seen += 1
        now = time.time()

        if pipeline in self._interval_rules:
            interval = self._interval_rules[pipeline]
            if (now - state.last_sampled_at) >= interval:
                state.last_sampled_at = now
                state.total_sampled += 1
                return SampleResult(metric=metric, sampled=True, reason="interval")
            return SampleResult(metric=metric, sampled=False, reason="interval")

        if pipeline in self._rate_rules:
            rate = self._rate_rules[pipeline]
            if random.random() < rate:
                state.last_sampled_at = now
                state.total_sampled += 1
                return SampleResult(metric=metric, sampled=True, reason="rate")
            return SampleResult(metric=metric, sampled=False, reason="rate")

        # No rule — always sample
        state.last_sampled_at = now
        state.total_sampled += 1
        return SampleResult(metric=metric, sampled=True, reason="always")

    def stats(self, pipeline: str) -> Optional[dict]:
        """Return sampling statistics for *pipeline*, or None if unseen."""
        state = self._state.get(pipeline)
        if state is None:
            return None
        return {
            "pipeline": pipeline,
            "total_seen": state.total_seen,
            "total_sampled": state.total_sampled,
            "sample_ratio": (
                round(state.total_sampled / state.total_seen, 4)
                if state.total_seen > 0 else 0.0
            ),
        }
