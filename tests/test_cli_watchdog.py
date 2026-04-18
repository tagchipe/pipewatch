"""Tests for cli_watchdog."""
from click.testing import CliRunner
from pipewatch.cli_watchdog import watchdog_cli
import json


def test_check_text_output():
    runner = CliRunner()
    result = runner.invoke(watchdog_cli, ["check"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output


def test_check_json_output():
    runner = CliRunner()
    result = runner.invoke(watchdog_cli, ["check", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3
    assert "is_dead" in data[0]


def test_dead_only_flag():
    runner = CliRunner()
    result = runner.invoke(watchdog_cli, ["check", "--dead-only"])
    assert result.exit_code == 0
    # ingest never reported, should appear
    assert "ingest" in result.output
    # transform reported recently, should not appear
    assert "transform" not in result.output


def test_dead_only_json():
    runner = CliRunner()
    result = runner.invoke(watchdog_cli, ["check", "--format", "json", "--dead-only"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert all(r["is_dead"] for r in data)
