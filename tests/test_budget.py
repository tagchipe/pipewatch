"""Tests for pipewatch.budget."""
import time
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.budget import BudgetTracker, BudgetResult


def make_metric(pipeline: str = "etl", status: MetricStatus = MetricStatus.OK, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(name="rows", pipeline=pipeline, value=value, status=status)


@pytest.fixture
def tracker() -> BudgetTracker:
    return BudgetTracker(default_max=3, default_window=60.0)


def test_check_returns_result(tracker):
    result = tracker.check("etl")
    assert isinstance(result, BudgetResult)
    assert result.pipeline == "etl"
    assert result.violation_count == 0
    assert not result.exceeded


def test_ok_metric_does_not_count(tracker):
    tracker.ingest(make_metric(status=MetricStatus.OK))
    assert tracker.check("etl").violation_count == 0


def test_warning_counts_as_violation(tracker):
    tracker.ingest(make_metric(status=MetricStatus.WARNING))
    assert tracker.check("etl").violation_count == 1


def test_critical_counts_as_violation(tracker):
    tracker.ingest(make_metric(status=MetricStatus.CRITICAL))
    assert tracker.check("etl").violation_count == 1


def test_budget_not_exceeded_below_max(tracker):
    for _ in range(3):
        tracker.ingest(make_metric(status=MetricStatus.WARNING))
    result = tracker.check("etl")
    assert result.violation_count == 3
    assert not result.exceeded


def test_budget_exceeded_above_max(tracker):
    for _ in range(4):
        tracker.ingest(make_metric(status=MetricStatus.CRITICAL))
    assert tracker.check("etl").exceeded


def test_register_custom_budget(tracker):
    tracker.register("slow", max_violations=1, window_seconds=60.0)
    tracker.ingest(make_metric(pipeline="slow", status=MetricStatus.WARNING))
    tracker.ingest(make_metric(pipeline="slow", status=MetricStatus.WARNING))
    assert tracker.check("slow").exceeded


def test_window_evicts_old_events():
    tracker = BudgetTracker(default_max=1, default_window=0.1)
    tracker.ingest(make_metric(status=MetricStatus.CRITICAL))
    tracker.ingest(make_metric(status=MetricStatus.CRITICAL))
    assert tracker.check("etl").exceeded
    time.sleep(0.15)
    assert not tracker.check("etl").exceeded


def test_to_dict(tracker):
    result = tracker.check("etl")
    d = result.to_dict()
    assert d["pipeline"] == "etl"
    assert "exceeded" in d
    assert "violation_count" in d
