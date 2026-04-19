"""Tests for pipewatch.cli_budget."""
import json
from click.testing import CliRunner
from pipewatch.cli_budget import budget_cli


def test_check_text_output():
    runner = CliRunner()
    result = runner.invoke(budget_cli, ["check"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output


def test_check_json_output():
    runner = CliRunner()
    result = runner.invoke(budget_cli, ["check", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert all("pipeline" in d for d in data)
    assert all("exceeded" in d for d in data)


def test_check_single_pipeline():
    runner = CliRunner()
    result = runner.invoke(budget_cli, ["check", "--pipeline", "ingest"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" not in result.output


def test_check_shows_exceeded():
    runner = CliRunner()
    result = runner.invoke(budget_cli, ["check", "--pipeline", "ingest"])
    assert "EXCEEDED" in result.output
