"""Report history for the Radon tool."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.radon.models import query_mi
from mq.web import DEFAULT_CHART_STYLE


def mi_h(args: Namespace, project: Project):
    """Create Pygal chart."""
    args.options.last = 9999
    timestamps, transposed, roc = query_mi(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Maintainability Index",
        dots_size=1,
        height=500,
        show_legend=False,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )

    dt_complexity = transposed["mi"]
    datetime_values = [(datetime.fromisoformat(timestamp), value) for timestamp, value in dt_complexity.items()]
    chart.add("-", datetime_values)

    return chart
