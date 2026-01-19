"""Render a histogram of file sizes."""

from pygal import Bar
from pygal.style import Style

from mq.tools.base import Scan
from mq.tools.cloc import DEFAULT_SCORING
from mq.tools.cloc.models import query
from mq.utils.scoring import find_grade
from mq.web import DEFAULT_CHART_STYLE


def cloc_f(scan: Scan):
    # Get bucket definitions from configuration for coloring
    buckets = DEFAULT_SCORING.get("cloc.histogram_file_size")["buckets"]

    histogram = query("f", scan=scan)

    # Values to chart are a combination of the respective value AND the color
    # (which is based on the configurable bucket definitions)
    chart_entries = []
    for bucket_label, count in histogram:  # e.g. (("100-199", 23), ("200+", 3))
        try:
            (lookup, _) = bucket_label.split("-")
        except ValueError:
            lookup = bucket_label.replace("+", "")

        _, color = find_grade(float(lookup), buckets)
        chart_entries.append(dict(value=count, color=color))

    chart = Bar(
        height=400,
        show_legend=False,
        style=Style(**DEFAULT_CHART_STYLE),
        title=None,
        tooltip_border_radius=10,
        y_title="Percent of Files by Total Lines",
        x_labels=[label for label, _ in histogram],
        value_formatter=lambda x: f"{x:.0f}%",  # Y-axis labels
        formatter=lambda x: f"{x:.1f}%",  # Tooltips when hovering
    )
    chart.add("File Size", chart_entries)

    return chart.render()
