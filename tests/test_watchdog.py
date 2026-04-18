"""Tests for pipewatch.watchdog."""
import time
from datetime import datetime
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.watchdog import Watchdog, WatchdogResult


def make_metric(pipeline: str = "etl") -> PipelineMetric:
    return PipelineMetric(
        name="row_count",
        pipeline=pipeline,
        value=100.0,
        status=MetricStatus.OK,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def watchdog() -> Watchdog:
    w = Watchdog()
    w.register("etl", timeout_seconds=1.0)
    w.register("load", timeout_seconds=60.0)
    return w


def test_unknown_pipeline_is_dead(watchdog):
    result = watchdog.check("etl")
    assert result.is_dead is True
    assert result.last_seen is None


def test_fresh_pipeline_not_dead(watchdog):
    watchdog.record(make_metric("etl"))
    result = watchdog.check("etl")
    assert result.is_dead is False


def test_stale_pipeline_is_dead(watchdog):
    watchdog.record(make_metric("etl"))
    time.sleep(1.1)
    result = watchdog.check("etl")
    assert result.is_dead is True


def test_check_all_returns_all_registered(watchdog):
    results = watchdog.check_all()
    pipelines = {r.pipeline for r in results}
    assert pipelines == {"etl", "load"}


def test_dead_pipelines_lists_dead(watchdog):
    watchdog.record(make_metric("load"))
    dead = watchdog.dead_pipelines()
    assert "etl" in dead
    assert "load" not in dead


def test_to_dict_keys(watchdog):
    result = watchdog.check("etl")
    d = result.to_dict()
    assert set(d.keys()) == {"pipeline", "last_seen", "timeout_seconds", "is_dead"}
