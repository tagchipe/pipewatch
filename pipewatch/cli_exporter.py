"""CLI command for exporting pipeline metrics."""
import click

from pipewatch.cli import _build_demo_collector
from pipewatch.exporter import MetricExporter


@click.group(name="export")
def exporter_cli() -> None:
    """Export pipeline metrics to CSV or JSON lines."""


@exporter_cli.command(name="run")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["csv", "jsonlines"]),
    default="csv",
    show_default=True,
    help="Output format.",
)
@click.option("--output", "-o", type=click.Path(), default=None, help="Write output to file.")
def export_cmd(fmt: str, output: str | None) -> None:
    """Collect metrics and export them."""
    collector = _build_demo_collector()
    exporter = MetricExporter()

    for metric in collector.evaluate():
        exporter.add(metric)

    if fmt == "csv":
        result = exporter.export_csv()
    else:
        result = exporter.export_jsonlines()

    if output:
        with open(output, "w") as fh:
            fh.write(result)
        click.echo(f"Exported to {output}")
    else:
        click.echo(result)
