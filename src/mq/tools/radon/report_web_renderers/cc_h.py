"""Report history for the Radon tool."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project

from mq.tools.radon.models import query_cc


def cc_h(args: Namespace, project: Project):
    """Create Pygal chart."""
    args.options.last = 9999
    timestamps, transposed, roc = query_cc(args, "h", project=project)

    custom_style = Style(
        background="transparent",
        font_family="Inter",
        guide_stroke_color="#cccccc",  # Lighter minor lines
        guide_stroke_dasharray="2,4",  # Different dash for minor
        guide_stroke_width=0.5,  # Thinner minor lines
        legend_font_size=10,
        major_guide_stroke_color="#333333",  # Darker major lines
        major_guide_stroke_dasharray="6,6",  # Dashed major lines
        major_guide_stroke_width=2,  # Thicker major lines
        transition="400ms ease-in",
    )

    chart = DateTimeLine(
        y_title="Complexity",
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=custom_style,
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
