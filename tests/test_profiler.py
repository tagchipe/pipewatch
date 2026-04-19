import pytest
from pipewatch.profiler import MetricProfiler, ProfileEntry
from pipewatch.metrics import PipelineMetric, MetricStatus
from datetime import datetime


def make_metric(pipeline: str, name: str, value: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        name=name,
        value=value,
        status=MetricStatus.OK,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def profiler() -> MetricProfiler:
    return MetricProfiler()


def test_get_returns_none_before_record(profiler):
    assert profiler.get("etl", "row_count") is None


def test_record_creates_entry(profiler):
    m = make_metric("etl", "row_count", 100.0)
    entry = profiler.record(m)
    assert isinstance(entry, ProfileEntry)
    assert entry.count == 1


def test_mean_single_value(profiler):
    profiler.record(make_metric("etl", "latency", 42.0))
    entry = profiler.get("etl", "latency")
    assert entry.mean == 42.0


def test_mean_multiple_values(profiler):
    for v in [10.0, 20.0, 30.0]:
        profiler.record(make_metric("etl", "latency", v))
    entry = profiler.get("etl", "latency")
    assert entry.mean == 20.0


def test_stddev_none_for_single(profiler):
    profiler.record(make_metric("etl", "latency", 5.0))
    assert profiler.get("etl", "latency").stddev is None


def test_stddev_computed(profiler):
    for v in [2.0, 4.0]:
        profiler.record(make_metric("etl", "latency", v))
    entry = profiler.get("etl", "latency")
    assert entry.stddev is not None
    assert entry.stddev > 0


def test_p95_returns_value(profiler):
    for v in range(1, 21):
        profiler.record(make_metric("etl", "rows", float(v)))
    entry = profiler.get("etl", "rows")
    assert entry.p95 is not None


def test_all_entries_multiple_pipelines(profiler):
    profiler.record(make_metric("etl", "rows", 1.0))
    profiler.record(make_metric("load", "rows", 2.0))
    assert len(profiler.all_entries()) == 2


def test_summary_returns_dicts(profiler):
    profiler.record(make_metric("etl", "rows", 5.0))
    s = profiler.summary()
    assert isinstance(s, list)
    assert "mean" in s[0]
    assert "p95" in s[0]
