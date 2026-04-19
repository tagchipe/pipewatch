"""Tests for pipewatch.rollup."""
import time
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.rollup import MetricRollup, RollupWindow


def make_metric(pipeline: str, name: str, value: float) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=MetricStatus.OK)


@pytest.fixture
def rollup() -> MetricRollup:
    return MetricRollup(window_seconds=60.0)


def test_get_returns_none_before_record(rollup):
    assert rollup.get("etl", "row_count") is None


def test_record_creates_window(rollup):
    m = make_metric("etl", "row_count", 100.0)
    win = rollup.record(m)
    assert win.pipeline == "etl"
    assert win.metric_name == "row_count"


def test_count_increments(rollup):
    m = make_metric("etl", "row_count", 10.0)
    rollup.record(m)
    rollup.record(m)
    win = rollup.get("etl", "row_count")
    assert win.count() == 2


def test_mean_single(rollup):
    rollup.record(make_metric("etl", "latency", 5.0))
    assert rollup.get("etl", "latency").mean() == pytest.approx(5.0)


def test_mean_multiple(rollup):
    for v in [2.0, 4.0, 6.0]:
        rollup.record(make_metric("etl", "latency", v))
    assert rollup.get("etl", "latency").mean() == pytest.approx(4.0)


def test_min_max(rollup):
    for v in [1.0, 5.0, 3.0]:
        rollup.record(make_metric("pipe", "errors", v))
    win = rollup.get("pipe", "errors")
    assert win.minimum() == pytest.approx(1.0)
    assert win.maximum() == pytest.approx(5.0)


def test_empty_window_returns_none():
    win = RollupWindow(pipeline="p", metric_name="m", window_seconds=60.0)
    assert win.mean() is None
    assert win.minimum() is None
    assert win.maximum() is None


def test_all_windows_returns_all(rollup):
    rollup.record(make_metric("a", "x", 1.0))
    rollup.record(make_metric("b", "y", 2.0))
    assert len(rollup.all_windows()) == 2


def test_to_dict_keys(rollup):
    rollup.record(make_metric("etl", "rows", 99.0))
    d = rollup.get("etl", "rows").to_dict()
    assert set(d.keys()) == {"pipeline", "metric_name", "window_seconds", "count", "mean", "min", "max"}


def test_prune_evicts_old_samples():
    win = RollupWindow(pipeline="p", metric_name="m", window_seconds=0.05)
    m = make_metric("p", "m", 42.0)
    win.add(m)
    assert win.count() == 1
    time.sleep(0.1)
    win.add(m)  # triggers prune; old sample should be gone
    assert win.count() == 1
