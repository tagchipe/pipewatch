"""Tests for pipewatch.cli_labeler."""
from click.testing import CliRunner
from pipewatch.cli_labeler import labeler_cli
import json


def test_list_text_output():
    runner = CliRunner()
    result = runner.invoke(labeler_cli, ["list"])
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "transform" in result.output


def test_list_json_output():
    runner = CliRunner()
    result = runner.invoke(labeler_cli, ["list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3
    assert "labels" in data[0]


def test_find_known_label():
    runner = CliRunner()
    result = runner.invoke(labeler_cli, ["find", "env", "prod"])
    assert result.exit_code == 0
    assert "ingest" in result.output


def test_find_unknown_label():
    runner = CliRunner()
    result = runner.invoke(labeler_cli, ["find", "env", "unknown-env"])
    assert result.exit_code == 0
    assert "No metrics found" in result.output


def test_find_json_output():
    runner = CliRunner()
    result = runner.invoke(labeler_cli, ["find", "team", "platform", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["pipeline"] == "transform"
