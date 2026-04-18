import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.pipeline_status import PipelineStatus, PipelineStatusBoard


def make_metric(pipeline: str, name: str, status: MetricStatus) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=1.0, status=status)


@pytest.fixture
def board():
    return PipelineStatusBoard()


def test_empty_board_returns_no_pipelines(board):
    assert board.all() == []


def test_ingest_groups_by_pipeline(board):
    metrics = [
        make_metric("etl_a", "rows", MetricStatus.OK),
        make_metric("etl_a", "lag", MetricStatus.WARNING),
        make_metric("etl_b", "rows", MetricStatus.OK),
    ]
    board.ingest(metrics)
    assert len(board.all()) == 2


def test_overall_status_ok(board):
    board.ingest([make_metric("etl_a", "rows", MetricStatus.OK)])
    assert board.get("etl_a").overall_status == MetricStatus.OK


def test_overall_status_warning(board):
    board.ingest([
        make_metric("etl_a", "rows", MetricStatus.OK),
        make_metric("etl_a", "lag", MetricStatus.WARNING),
    ])
    assert board.get("etl_a").overall_status == MetricStatus.WARNING


def test_overall_status_critical_beats_warning(board):
    board.ingest([
        make_metric("etl_a", "lag", MetricStatus.WARNING),
        make_metric("etl_a", "errors", MetricStatus.CRITICAL),
    ])
    assert board.get("etl_a").overall_status == MetricStatus.CRITICAL


def test_critical_pipelines_filter(board):
    board.ingest([
        make_metric("etl_a", "rows", MetricStatus.OK),
        make_metric("etl_b", "errors", MetricStatus.CRITICAL),
    ])
    critical = board.critical_pipelines()
    assert len(critical) == 1
    assert critical[0].pipeline == "etl_b"


def test_get_unknown_pipeline_returns_none(board):
    assert board.get("missing") is None


def test_to_dict_includes_all_pipelines(board):
    board.ingest([
        make_metric("etl_a", "rows", MetricStatus.OK),
        make_metric("etl_b", "rows", MetricStatus.WARNING),
    ])
    d = board.to_dict()
    assert "etl_a" in d
    assert "etl_b" in d
    assert d["etl_b"]["overall_status"] == "warning"
