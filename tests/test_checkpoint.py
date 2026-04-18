"""Tests for pipewatch.checkpoint."""
import json
import time
import pytest
from pipewatch.checkpoint import CheckpointStore, CheckpointEntry


@pytest.fixture
def store():
    return CheckpointStore()


def test_record_returns_entry(store):
    entry = store.record("etl.sales")
    assert isinstance(entry, CheckpointEntry)
    assert entry.pipeline == "etl.sales"


def test_get_returns_none_for_unknown(store):
    assert store.get("missing") is None


def test_get_returns_recorded(store):
    store.record("etl.orders", metadata={"rows": 100})
    entry = store.get("etl.orders")
    assert entry is not None
    assert entry.metadata["rows"] == 100


def test_age_seconds_is_small(store):
    store.record("etl.users")
    entry = store.get("etl.users")
    assert entry.age_seconds() < 2.0


def test_all_returns_all_entries(store):
    store.record("a")
    store.record("b")
    names = {e.pipeline for e in store.all()}
    assert names == {"a", "b"}


def test_to_dict_keys(store):
    store.record("etl.x", metadata={"source": "s3"})
    d = store.get("etl.x").to_dict()
    assert set(d.keys()) == {"pipeline", "last_success", "age_seconds", "metadata"}


def test_persists_to_file(tmp_path):
    p = tmp_path / "checkpoints.json"
    s1 = CheckpointStore(str(p))
    s1.record("etl.persist", metadata={"v": 42})
    s2 = CheckpointStore(str(p))
    entry = s2.get("etl.persist")
    assert entry is not None
    assert entry.metadata["v"] == 42


def test_overwrite_updates_timestamp(store):
    store.record("etl.z")
    t1 = store.get("etl.z").last_success
    time.sleep(0.05)
    store.record("etl.z")
    t2 = store.get("etl.z").last_success
    assert t2 > t1
