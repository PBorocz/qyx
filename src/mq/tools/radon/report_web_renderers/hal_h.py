"""Report history for the Radon tool."""

from datetime import datetime

from pygal import DateTimeLine
from pygal.style import Style

from mq.tools.base import Project
from mq.tools.radon.models import query_hal, RadonHal
from mq.web import DEFAULT_CHART_STYLE


def hal_h(project: Project):
    timestamps, transposed, _ = query_hal("h", project=project)

    style = Style(**DEFAULT_CHART_STYLE)

    # Create a chart for EACH separate metric!
    charts = dict()
    radon_names = {attr[1]: attr[0].split("(")[0] for attr in RadonHal.attrs()}
    for metric, values_by_timestamp in transposed.items():
        dt_values = [(datetime.fromisoformat(ts_), value) for ts_, value in values_by_timestamp.items()]
        chart = DateTimeLine(
            y_title=radon_names[metric],
            dots_size=1,
            height=500,
            show_legend=False,
            style=style,
            tooltip_border_radius=10,
            x_label_rotation=45,  # Angle labels to prevent overlap
            x_labels_major_every=2,  # Show every 5th label
            x_value_formatter=lambda dt: dt.strftime("%Y-%m-%d %H:%M"),
        )
        chart.add(metric, dt_values)
        charts[metric] = chart

    return charts
