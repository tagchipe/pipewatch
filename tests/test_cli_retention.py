"""Tests for pipewatch.cli_retention."""
from click.testing import CliRunner
from pipewatch.cli_retention import retention_cli
import json


def test_apply_text_output():
    runner = CliRunner()
    result = runner.invoke(retention_cli, ["apply", "--format", "text"])
    assert result.exit_code == 0
    assert "Kept" in result.output
    assert "Evicted" in result.output


def test_apply_json_output():
    runner = CliRunner()
    result = runner.invoke(retention_cli, ["apply", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "kept" in data
    assert "evicted" in data


def test_apply_evicts_old_metrics():
    runner = CliRunner()
    result = runner.invoke(retention_cli, ["apply", "--format", "json"])
    data = json.loads(result.output)
    assert data["evicted"] >= 1


def test_apply_keeps_fresh_metrics():
    runner = CliRunner()
    result = runner.invoke(retention_cli, ["apply", "--format", "json"])
    data = json.loads(result.output)
    assert data["kept"] >= 1
