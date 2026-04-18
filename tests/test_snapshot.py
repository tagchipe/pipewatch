"""Tests for pipewatch.snapshot."""
from datetime import datetime
import pytest

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.snapshot import SnapshotManager, Snapshot, DiffEntry


def make_metric(pipeline: str, name: str, value: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def manager():
    return SnapshotManager()


def test_capture_returns_snapshot(manager):
    metrics = [make_metric("etl", "rows", 100)]
    snap = manager.capture("s1", metrics)
    assert isinstance(snap, Snapshot)
    assert snap.name == "s1"
    assert len(snap.metrics) == 1


def test_get_returns_captured(manager):
    metrics = [make_metric("etl", "rows", 100)]
    manager.capture("s1", metrics)
    snap = manager.get("s1")
    assert snap is not None
    assert snap.name == "s1"


def test_get_missing_returns_none(manager):
    assert manager.get("nope") is None


def test_diff_detects_change(manager):
    manager.capture("before", [make_metric("etl", "rows", 100)])
    manager.capture("after", [make_metric("etl", "rows", 150)])
    diffs = manager.diff("before", "after")
    assert len(diffs) == 1
    assert diffs[0].delta == pytest.approx(50)


def test_diff_detects_new_metric(manager):
    manager.capture("before", [make_metric("etl", "rows", 100)])
    manager.capture("after", [
        make_metric("etl", "rows", 100),
        make_metric("etl", "errors", 5),
    ])
    diffs = manager.diff("before", "after")
    new = next(d for d in diffs if d.metric_name == "errors")
    assert new.before is None
    assert new.after == 5


def test_diff_missing_snapshot_returns_empty(manager):
    manager.capture("before", [make_metric("etl", "rows", 100)])
    assert manager.diff("before", "missing") == []


def test_to_dict_structure(manager):
    manager.capture("s1", [make_metric("etl", "rows", 10)])
    d = manager.get("s1").to_dict()
    assert "name" in d
    assert "captured_at" in d
    assert "metrics" in d
    assert isinstance(d["metrics"], list)
