"""Tests for pipewatch.tagging."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.tagging import TagIndex, TagManager


def make_metric(name: str, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        name=name,
        pipeline="pipe",
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def manager() -> TagManager:
    return TagManager()


def test_tag_and_retrieve(manager):
    m = make_metric("rows_loaded")
    manager.tag(m, ["etl", "daily"])
    assert "etl" in manager.get_tags(m)
    assert "daily" in manager.get_tags(m)


def test_by_tag_returns_metrics(manager):
    m1 = make_metric("rows_loaded")
    m2 = make_metric("error_rate")
    manager.tag(m1, ["etl"])
    manager.tag(m2, ["etl", "quality"])
    result = manager.by_tag("etl")
    assert m1 in result
    assert m2 in result


def test_by_tag_missing_returns_empty(manager):
    assert manager.by_tag("nonexistent") == []


def test_all_tags(manager):
    m = make_metric("latency")
    manager.tag(m, ["perf", "sla"])
    tags = manager.all_tags()
    assert "perf" in tags
    assert "sla" in tags


def test_no_duplicate_tags(manager):
    m = make_metric("rows_loaded")
    manager.tag(m, ["etl"])
    manager.tag(m, ["etl", "daily"])
    tags = manager.get_tags(m)
    assert tags.count("etl") == 1


def test_tag_index_tags_for(manager):
    m = make_metric("volume")
    manager.tag(m, ["batch"])
    index_tags = manager._index.tags_for(m)
    assert "batch" in index_tags
