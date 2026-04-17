"""Tests for pipewatch.cli_baseline."""
from click.testing import CliRunner
from pipewatch.cli_baseline import baseline_cli
import json


def test_check_text_output():
    runner = CliRunner()
    result = runner.invoke(baseline_cli, ["check"])
    assert result.exit_code == 0
    assert "/" in result.output  # pipeline/name format


def test_check_json_output():
    runner = CliRunner()
    result = runner.invoke(baseline_cli, ["check", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "within_baseline" in data[0]


def test_only_violations_flag():
    runner = CliRunner()
    result = runner.invoke(baseline_cli, ["check", "--only-violations", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert all(not r["within_baseline"] for r in data)


def test_check_text_contains_status_label():
    runner = CliRunner()
    result = runner.invoke(baseline_cli, ["check"])
    assert "OK" in result.output or "VIOLATION" in result.output
