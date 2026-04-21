"""Tests for pipewatch.sampler."""
import time

import pytest

from pipewatch.metrics import MetricStatus, PipelineMetric
from pipewatch.sampler import MetricSampler


def make_metric(pipeline: str = "etl", value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        name="row_count",
        pipeline=pipeline,
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def sampler() -> MetricSampler:
    return MetricSampler()


# --- always-sample (no rule) ---

def test_no_rule_always_sampled(sampler):
    result = sampler.check(make_metric("pipe_a"))
    assert result.sampled is True
    assert result.reason == "always"


# --- rate-based sampling ---

def test_rate_1_always_accepted(sampler):
    sampler.register_rate("pipe_b", 1.0)
    for _ in range(20):
        result = sampler.check(make_metric("pipe_b"))
        assert result.sampled is True
        assert result.reason == "rate"


def test_rate_0_always_rejected(sampler):
    sampler.register_rate("pipe_c", 0.0)
    for _ in range(20):
        result = sampler.check(make_metric("pipe_c"))
        assert result.sampled is False
        assert result.reason == "rate"


def test_invalid_rate_raises(sampler):
    with pytest.raises(ValueError):
        sampler.register_rate("pipe_x", 1.5)


# --- interval-based sampling ---

def test_interval_first_check_accepted(sampler):
    sampler.register_interval("pipe_d", 60.0)
    result = sampler.check(make_metric("pipe_d"))
    assert result.sampled is True
    assert result.reason == "interval"


def test_interval_second_check_blocked(sampler):
    sampler.register_interval("pipe_e", 60.0)
    sampler.check(make_metric("pipe_e"))  # first — accepted
    result = sampler.check(make_metric("pipe_e"))  # second — blocked
    assert result.sampled is False
    assert result.reason == "interval"


def test_interval_accepted_after_window(sampler):
    sampler.register_interval("pipe_f", 0.05)
    sampler.check(make_metric("pipe_f"))  # first
    time.sleep(0.1)
    result = sampler.check(make_metric("pipe_f"))
    assert result.sampled is True


def test_invalid_interval_raises(sampler):
    with pytest.raises(ValueError):
        sampler.register_interval("pipe_y", -1.0)


# --- stats ---

def test_stats_none_for_unseen(sampler):
    assert sampler.stats("ghost") is None


def test_stats_tracks_counts(sampler):
    sampler.register_rate("pipe_g", 1.0)
    for _ in range(5):
        sampler.check(make_metric("pipe_g"))
    s = sampler.stats("pipe_g")
    assert s["total_seen"] == 5
    assert s["total_sampled"] == 5
    assert s["sample_ratio"] == 1.0


def test_stats_ratio_with_zero_rate(sampler):
    sampler.register_rate("pipe_h", 0.0)
    for _ in range(4):
        sampler.check(make_metric("pipe_h"))
    s = sampler.stats("pipe_h")
    assert s["total_seen"] == 4
    assert s["total_sampled"] == 0
    assert s["sample_ratio"] == 0.0
