"""Tests for pipewatch.labeler."""
import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.labeler import MetricLabeler, LabelSet


def make_metric(name: str = "row_count", pipeline: str = "etl", value: float = 100.0) -> PipelineMetric:
    return PipelineMetric(
        name=name,
        pipeline=pipeline,
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def labeler() -> MetricLabeler:
    return MetricLabeler()


def test_label_returns_label_set(labeler):
    m = make_metric()
    ls = labeler.label(m, env="prod", team="data")
    assert isinstance(ls, LabelSet)
    assert ls.get("env") == "prod"
    assert ls.get("team") == "data"


def test_get_labels_returns_none_for_unknown(labeler):
    m = make_metric()
    assert labeler.get_labels(m) is None


def test_get_labels_returns_set_after_labelling(labeler):
    m = make_metric()
    labeler.label(m, env="staging")
    ls = labeler.get_labels(m)
    assert ls is not None
    assert ls.get("env") == "staging"


def test_label_accumulates_across_calls(labeler):
    m = make_metric()
    labeler.label(m, env="prod")
    labeler.label(m, team="platform")
    ls = labeler.get_labels(m)
    assert ls.get("env") == "prod"
    assert ls.get("team") == "platform"


def test_find_by_label_returns_matching(labeler):
    m1 = make_metric(name="rows", pipeline="pipe_a")
    m2 = make_metric(name="latency", pipeline="pipe_b")
    labeler.label(m1, env="prod")
    labeler.label(m2, env="dev")
    results = labeler.find_by_label("env", "prod")
    assert len(results) == 1
    assert results[0].pipeline == "pipe_a"


def test_find_by_label_returns_empty_when_no_match(labeler):
    m = make_metric()
    labeler.label(m, env="prod")
    assert labeler.find_by_label("env", "staging") == []


def test_remove_label_deletes_key(labeler):
    m = make_metric()
    labeler.label(m, env="prod", team="data")
    labeler.remove_label(m, "env")
    ls = labeler.get_labels(m)
    assert ls.get("env") is None
    assert ls.get("team") == "data"


def test_remove_label_on_unknown_metric_is_safe(labeler):
    m = make_metric()
    labeler.remove_label(m, "env")  # should not raise


def test_all_label_sets_returns_all(labeler):
    m1 = make_metric(name="rows", pipeline="p1")
    m2 = make_metric(name="errors", pipeline="p2")
    labeler.label(m1, env="prod")
    labeler.label(m2, env="dev")
    assert len(labeler.all_label_sets()) == 2


def test_to_dict_contains_expected_keys(labeler):
    m = make_metric()
    labeler.label(m, env="prod")
    d = labeler.get_labels(m).to_dict()
    assert "metric_name" in d
    assert "pipeline" in d
    assert "labels" in d
    assert d["labels"]["env"] == "prod"
