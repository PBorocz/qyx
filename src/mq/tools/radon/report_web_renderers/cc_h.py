"""Report history for the Radon tool."""

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.radon.models import query_cc
from mq.web import DEFAULT_CHART_STYLE


def cc_h(project: Project):
    """Create Pygal chart."""
    timestamps, transposed, roc = query_cc("h", project=project, last=None)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Complexity",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )

    for metric, display in (
        ("Class", "Classes"),
        ("Function", "Functions"),
        ("Method", "Methods"),
    ):
        values_by_timestamp = transposed[metric]
        datetime_values = [(datetime.fromisoformat(ts_), value) for ts_, value in values_by_timestamp.items()]
        chart.add(display, datetime_values)

    return chart
