"""Summary builder that combines reporter output with aggregated stats."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import json

from pipewatch.reporter import Reporter, PipelineReport
from pipewatch.aggregator import MetricAggregator, AggregatedStats
from pipewatch.metrics import MetricStatus


@dataclass
class PipelineSummary:
    report: PipelineReport
    stats: List[AggregatedStats] = field(default_factory=list)

    @property
    def overall_status(self) -> MetricStatus:
        return self.report.overall_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "report": self.report.to_dict(),
            "aggregated_stats": [s.to_dict() for s in self.stats],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class SummaryBuilder:
    """Combines a Reporter and a MetricAggregator into a PipelineSummary."""

    def __init__(self, reporter: Reporter, aggregator: MetricAggregator):
        self.reporter = reporter
        self.aggregator = aggregator

    def build(self) -> PipelineSummary:
        report = self.reporter.generate()
        stats = self.aggregator.all_stats()
        return PipelineSummary(report=report, stats=stats)
