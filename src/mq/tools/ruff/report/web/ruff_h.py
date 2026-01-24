"""Report data obo running 'ruff' tool."""

from argparse import Namespace

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.ruff.models import query
from mq.web import DEFAULT_CHART_STYLE


def ruff_h(args: Namespace, project: Project):
    # Create Pygal chart
    _, rows, _ = query(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Ruff Issues",
        dots_size=1,
        height=500,
        show_legend=False,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in rows.items()]

    chart.add("-count-", datetime_values)

    return chart.render()  # Render as SVG and return bytes
