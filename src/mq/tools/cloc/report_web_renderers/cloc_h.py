"""Report data obo running 'cloc' tool for level h."""

from argparse import Namespace
from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.cloc.models import query


def cloc_h(args: Namespace, project: Project):
    # Create Pygal chart
    args.options.last = 999  # Override to get ALL the data we have!
    _, rows, _, _, _, _ = query(args, "history", project=project)

    custom_style = Style(
        background="transparent",
        font_family="Inter",
        guide_stroke_color="#cccccc",  # Lighter minor lines
        guide_stroke_dasharray="2,4",  # Different dash for minor
        guide_stroke_width=0.5,  # Thinner minor lines
        major_guide_stroke_color="#333333",  # Darker major lines
        major_guide_stroke_dasharray="6,6",  # Dashed major lines
        major_guide_stroke_width=2,  # Thicker major lines
        transition="400ms ease-in",
    )

    chart = DateTimeLine(
        y_title="Lines",
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
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("Code", datetime_values_cd)
    chart.add("Comments", datetime_values_cm)
    chart.add("Blanks", datetime_values_bl)

    return chart.render()  # Render as SVG and return bytes
