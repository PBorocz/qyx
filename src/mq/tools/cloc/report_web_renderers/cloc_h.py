"""Report data obo running 'cloc' tool for level h."""

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.cloc.models import query
from mq.web import DEFAULT_CHART_STYLE


def cloc_h(project: Project):
    # Create Pygal chart
    _, rows, _, _, _, _ = query("history", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    chart = DateTimeLine(
        dots_size=1,
        height=500,
        legend_at_bottom=True,
        legend_at_bottom_columns=3,
        style=style,
        tooltip_border_radius=10,
        x_label_rotation=45,  # Angle labels to prevent overlap
        x_labels_major_every=2,  # Show every 5th label
        x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
        y_title="Lines",
    )
    datetime_values_cd = [(datetime.fromisoformat(row.timestamp), row.total_code) for row in rows]
    datetime_values_cm = [(datetime.fromisoformat(row.timestamp), row.total_comment) for row in rows]
    datetime_values_bl = [(datetime.fromisoformat(row.timestamp), row.total_blank) for row in rows]

    chart.add("Code", datetime_values_cd)
    chart.add("Comments", datetime_values_cm)
    chart.add("Blanks", datetime_values_bl)

    return chart.render()  # Render as SVG and return bytes
