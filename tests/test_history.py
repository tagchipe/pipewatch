"""Tests for pipewatch.history module."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.history import MetricHistory, HistoryTracker


def make_metric(value: float, pipeline: str = "etl", name: str = "row_count") -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        name=name,
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def tracker() -> HistoryTracker:
    return HistoryTracker(max_size=5)


def test_record_and_retrieve(tracker):
    tracker.record(make_metric(10.0))
    history = tracker.get("etl", "row_count")
    assert history is not None
    assert history.latest().value == 10.0


def test_values_accumulate(tracker):
    for v in [1.0, 2.0, 3.0]:
        tracker.record(make_metric(v))
    assert tracker.get("etl", "row_count").values() == [1.0, 2.0, 3.0]


def test_max_size_evicts_oldest(tracker):
    for v in range(7):
        tracker.record(make_metric(float(v)))
    history = tracker.get("etl", "row_count")
    assert len(history.values()) == 5
    assert history.values()[0] == 2.0


def test_trend_up(tracker):
    for v in [1.0, 2.0, 3.0]:
        tracker.record(make_metric(v))
    assert tracker.get("etl", "row_count").trend() == "up"


def test_trend_down(tracker):
    for v in [3.0, 2.0, 1.0]:
        tracker.record(make_metric(v))
    assert tracker.get("etl", "row_count").trend() == "down"


def test_trend_stable(tracker):
    for v in [5.0, 5.0, 5.0]:
        tracker.record(make_metric(v))
    assert tracker.get("etl", "row_count").trend() == "stable"


def test_trend_none_when_single_entry(tracker):
    tracker.record(make_metric(1.0))
    assert tracker.get("etl", "row_count").trend() is None


def test_get_missing_returns_none(tracker):
    assert tracker.get("missing", "metric") is None


def test_all_histories(tracker):
    tracker.record(make_metric(1.0, pipeline="p1", name="m1"))
    tracker.record(make_metric(2.0, pipeline="p2", name="m2"))
    assert len(tracker.all_histories()) == 2


def test_to_dict(tracker):
    tracker.record(make_metric(42.0))
    d = tracker.get("etl", "row_count").to_dict()
    assert d["pipeline"] == "etl"
    assert d["latest"] == 42.0
    assert d["count"] == 1
