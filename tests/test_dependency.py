import pytest
from pipewatch.dependency import DependencyGraph
from pipewatch.metrics import MetricStatus


@pytest.fixture
def graph() -> DependencyGraph:
    g = DependencyGraph()
    g.register("ingest")
    g.register("transform", upstream=["ingest"])
    g.register("load", upstream=["transform"])
    return g


def test_upstream_direct(graph):
    assert graph.upstream_of("transform") == ["ingest"]


def test_upstream_missing_returns_empty(graph):
    assert graph.upstream_of("unknown") == []


def test_all_upstream_transitive(graph):
    result = graph.all_upstream("load")
    assert "ingest" in result
    assert "transform" in result


def test_evaluate_ok_when_all_ok(graph):
    statuses = {"ingest": MetricStatus.OK, "transform": MetricStatus.OK, "load": MetricStatus.OK}
    result = graph.evaluate("load", statuses)
    assert result.propagated_status == MetricStatus.OK
    assert result.blocking_pipelines == []


def test_evaluate_propagates_critical(graph):
    statuses = {"ingest": MetricStatus.CRITICAL, "transform": MetricStatus.OK, "load": MetricStatus.OK}
    result = graph.evaluate("load", statuses)
    assert result.propagated_status == MetricStatus.CRITICAL
    assert "ingest" in result.blocking_pipelines


def test_evaluate_propagates_warning(graph):
    statuses = {"ingest": MetricStatus.WARNING, "transform": MetricStatus.OK, "load": MetricStatus.OK}
    result = graph.evaluate("load", statuses)
    assert result.propagated_status == MetricStatus.WARNING


def test_direct_status_preserved(graph):
    statuses = {"ingest": MetricStatus.OK, "transform": MetricStatus.OK, "load": MetricStatus.CRITICAL}
    result = graph.evaluate("load", statuses)
    assert result.direct_status == MetricStatus.CRITICAL
    assert result.propagated_status == MetricStatus.CRITICAL


def test_to_dict(graph):
    statuses = {"ingest": MetricStatus.OK, "transform": MetricStatus.OK, "load": MetricStatus.OK}
    d = graph.evaluate("load", statuses).to_dict()
    assert d["pipeline"] == "load"
    assert "propagated_status" in d
