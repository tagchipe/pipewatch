"""Tests for pipewatch.staleness."""
import time
import pytest
from pipewatch.checkpoint import CheckpointStore
from pipewatch.staleness import StalenessChecker, StalenessResult


@pytest.fixture
def store():
    return CheckpointStore()


@pytest.fixture
def checker(store):
    return StalenessChecker(store)


def test_unknown_pipeline_is_stale(checker):
    checker.register("etl.x", max_age_seconds=60)
    result = checker.check("etl.x")
    assert result.is_stale is True
    assert result.age_seconds == float("inf")


def test_fresh_pipeline_not_stale(store, checker):
    store.record("etl.fresh")
    checker.register("etl.fresh", max_age_seconds=3600)
    result = checker.check("etl.fresh")
    assert result.is_stale is False


def test_old_pipeline_is_stale(store, checker):
    store.record("etl.old")
    checker.register("etl.old", max_age_seconds=0.01)
    time.sleep(0.05)
    result = checker.check("etl.old")
    assert result.is_stale is True


def test_check_all_returns_all_registered(store, checker):
    store.record("a")
    store.record("b")
    checker.register("a", 3600)
    checker.register("b", 3600)
    results = checker.check_all()
    assert len(results) == 2


def test_stale_pipelines_filters(store, checker):
    store.record("ok")
    checker.register("ok", 3600)
    checker.register("missing", 60)
    stale = checker.stale_pipelines()
    assert any(r.pipeline == "missing" for r in stale)
    assert all(r.pipeline != "ok" for r in stale)


def test_to_dict_keys(store, checker):
    store.record("etl.d")
    checker.register("etl.d", 3600)
    d = checker.check("etl.d").to_dict()
    assert set(d.keys()) == {"pipeline", "age_seconds", "max_age_seconds", "is_stale"}
