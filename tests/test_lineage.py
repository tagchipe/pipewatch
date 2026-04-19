import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.lineage import LineageEntry, LineageTracker


def make_metric(pipeline: str = "etl", name: str = "row_count", value: float = 100.0) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=MetricStatus.OK)


@pytest.fixture
def tracker() -> LineageTracker:
    return LineageTracker()


def test_record_returns_entry(tracker):
    m = make_metric()
    entry = tracker.record(m, source="kafka", tags={"env": "prod"})
    assert isinstance(entry, LineageEntry)
    assert entry.pipeline == "etl"
    assert entry.metric_name == "row_count"
    assert entry.source == "kafka"
    assert entry.tags == {"env": "prod"}


def test_get_returns_recorded(tracker):
    m = make_metric()
    tracker.record(m, source="s3")
    entry = tracker.get("etl", "row_count")
    assert entry is not None
    assert entry.source == "s3"


def test_get_returns_none_for_unknown(tracker):
    assert tracker.get("missing", "metric") is None


def test_all_entries(tracker):
    tracker.record(make_metric("p1", "m1"), source="a")
    tracker.record(make_metric("p2", "m2"), source="b")
    assert len(tracker.all_entries()) == 2


def test_by_source_filters(tracker):
    tracker.record(make_metric("p1", "m1"), source="kafka")
    tracker.record(make_metric("p2", "m2"), source="s3")
    tracker.record(make_metric("p3", "m3"), source="kafka")
    results = tracker.by_source("kafka")
    assert len(results) == 2
    assert all(e.source == "kafka" for e in results)


def test_by_source_empty_when_no_match(tracker):
    tracker.record(make_metric(), source="s3")
    assert tracker.by_source("kafka") == []


def test_to_dict_shape(tracker):
    m = make_metric()
    entry = tracker.record(m, source="db", tags={"region": "us-east"})
    d = entry.to_dict()
    assert set(d.keys()) == {"pipeline", "metric_name", "source", "tags"}


def test_to_json_is_valid(tracker):
    import json
    tracker.record(make_metric("p1", "m1"), source="x")
    data = json.loads(tracker.to_json())
    assert isinstance(data, list)
    assert data[0]["pipeline"] == "p1"
