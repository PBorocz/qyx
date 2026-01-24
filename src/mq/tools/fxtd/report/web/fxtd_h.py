"""Report data obo running 'fxtd' tool/script for level h."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.fxtd.models import query
from mq.web import DEFAULT_CHART_STYLE


def fxtd_h(args: Namespace, project: Project):
    # Create Pygal chart
    timestamps, transposed, rocs = query(args, "h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        y_title="Instances",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
    )
    for metric in ("FIXME", "TODO"):
        dt_values = transposed[metric]
        datetime_values = [(datetime.fromisoformat(ts_), count) for ts_, count in dt_values.items()]
        chart.add(metric, datetime_values)

    return chart.render()  # Render as SVG and return bytes
