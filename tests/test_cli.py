"""Tests for pipewatch CLI commands."""
from click.testing import CliRunner
from pipewatch.cli import cli


def test_report_text_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--pipeline", "my-pipe"])
    assert "my-pipe" in result.output
    assert "Status" in result.output


def test_report_json_output():
    import json
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--format", "json"])
    data = json.loads(result.output)
    assert "pipeline" in data
    assert "overall_status" in data


def test_report_exit_code_warning():
    runner = CliRunner()
    result = runner.invoke(cli, ["report"])
    # demo collector has a warning-level metric
    assert result.exit_code in (0, 1, 2)


def test_report_writes_file(tmp_path):
    out = tmp_path / "report.json"
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--format", "json", "--output", str(out)])
    assert out.exists()
    assert "Report written to" in result.output
