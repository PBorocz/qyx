"""Report history for the Radon tool - Raw analysis."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.radon.models import query_raw
from mq.web import DEFAULT_CHART_STYLE


def raw_h(args: Namespace, project: Project):
    """Create Pygal chart."""
    args.options.last = 9999
    timestamps, transposed, rocs, roc_gt = query_raw(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Lines",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every other label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )

    for metric, dt_rows in transposed.items():
        datetime_values = [(datetime.fromisoformat(timestamp), value) for timestamp, value in dt_rows.items()]
        chart.add(metric.upper(), datetime_values)

    return chart
