import pytest
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.replay import MetricReplayer, ReplayResult


def make_metric(name: str, pipeline: str, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        name=name,
        pipeline=pipeline,
        value=value,
        status=MetricStatus.OK,
    )


@pytest.fixture
def received():
    return []


@pytest.fixture
def replayer(received):
    return MetricReplayer(handler=received.append)


def test_replay_all(replayer, received):
    replayer.load([make_metric("m1", "pipe_a"), make_metric("m2", "pipe_b")])
    result = replayer.replay()
    assert result.replayed == 2
    assert len(received) == 2


def test_replay_filtered_by_pipeline(replayer, received):
    replayer.load([
        make_metric("m1", "pipe_a"),
        make_metric("m2", "pipe_b"),
        make_metric("m3", "pipe_a"),
    ])
    result = replayer.replay(pipeline="pipe_a")
    assert result.replayed == 2
    assert result.skipped == 1
    assert all(m.pipeline == "pipe_a" for m in received)


def test_replay_with_limit(replayer, received):
    replayer.load([make_metric(f"m{i}", "pipe_a") for i in range(10)])
    result = replayer.replay(limit=3)
    assert result.replayed == 3
    assert len(received) == 3


def test_buffered_count(replayer):
    assert replayer.buffered == 0
    replayer.load([make_metric("m1", "pipe_a")])
    assert replayer.buffered == 1


def test_clear_empties_buffer(replayer):
    replayer.load([make_metric("m1", "pipe_a")])
    replayer.clear()
    assert replayer.buffered == 0


def test_result_to_dict():
    r = ReplayResult(replayed=5, skipped=2, pipeline="pipe_x")
    d = r.to_dict()
    assert d["replayed"] == 5
    assert d["skipped"] == 2
    assert d["pipeline"] == "pipe_x"


def test_replay_empty_buffer(replayer, received):
    result = replayer.replay()
    assert result.replayed == 0
    assert received == []
