"""Web rendering obo 'cloc' tool."""

from argparse import Namespace
from datetime import datetime

import plotly.graph_objects as go
from bottle import request

from qyx.tools.base import Scan, State
from qyx.tools.cloc.models import query_0, query_1, query_2, query_d, query_f, query_h
from qyx.utils.scoring import find_grade
from qyx.web.page import generic_render, generic_render_scans, render_partial
from qyx.web.plotly import SERIES_COLORS, custom_labels, style_figure


################################################################################################
# Page layout...
################################################################################################
def render(template: str = "cloc::page.html") -> str:
    """Render the primary page layout for this tools display page."""
    return generic_render("cloc", template, get_content)


def render_scans(template: str = "base::_select_scan.cascading.html") -> str:
    """Render the scan select widget based on a new project selection."""
    return generic_render_scans("cloc")


def render_content(template: str = "cloc::body.htmx"):
    s_scan_id = request.query.scan
    scan = Scan.get_or_none(Scan.id == int(s_scan_id)) if s_scan_id else None
    if not scan:
        return render_partial("base::_no_scans_yet.htmx")
    context = get_content(scan)
    return render_partial(template, **context.__dict__)


################################################################################################
def get_content(scan: Scan):
    """Populate our tool's home page to the specified scan."""
    State.update(
        request.app.args,
        project=scan.request.project.name,
        analysis="cloc",
    )

    context = Namespace()
    context.cloc_as_of = scan.as_of_display(collapse_today=True)
    context.cloc_0 = query_0(scan)
    context.cloc_1 = query_1(scan)
    context.cloc_2 = query_2(scan)
    context.cloc_d = query_d(request.app.args, scan)
    context.cloc_f = cloc_f(request.app.args, scan)
    context.cloc_h = cloc_h(request.app.args, scan)
    return context


################################################################################################
def cloc_f(args: Namespace, scan: Scan):
    # Get bucket definitions from configuration for coloring
    buckets = args.config.get("tools.cloc.histogram_file_size.buckets")
    histogram = query_f(args, scan)

    # Values to chart are a combination of the respective value AND the color
    # (which is based on the configurable bucket definitions)
    chart_entries = []
    for bucket_label, count in histogram:  # e.g. (("100-199", 23.5), ("200+", 30.4))
        try:
            (lookup, _) = bucket_label.split("-")
        except ValueError:
            lookup = bucket_label.replace("+", "")

        _, color = find_grade(float(lookup), buckets)
        chart_entries.append(dict(value=int(count), color=color))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[label for label, _ in histogram],
            y=[entry["value"] for entry in chart_entries],
            marker_color=[entry["color"] for entry in chart_entries],
            hovertemplate="%{y}% " + "of files are <b>%{x}</b> lines long<br>" + "<extra></extra>",
        ),
    )

    style_figure(
        fig,
        layout={
            "xaxis": None,
            "yaxis_title": "Percent of Files by Total Lines",
        },
    )
    return fig.to_html()


def cloc_h(args: Namespace, scan: Scan) -> bytes | None:
    result = query_h(scan.request.project)
    if not result.rows:
        return None

    metric_titles = (
        ("total_code", "Total Code Lines"),
        ("total_comment", "Total Comment Lines"),
        ("total_blank", "Total Blank Lines"),
    )
    fig = go.Figure()
    for i, (metric, title) in enumerate(metric_titles):
        x_values = [datetime.fromisoformat(row.timestamp) for row in result.rows]
        y_values = [getattr(row, metric) for row in result.rows]

        # We want custom hover labels based on the respective git messages
        labels = custom_labels(title, result.messages, x_values, y_values)

        # Add a series for each specific metric
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                name=title,
                marker=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], size=4, opacity=0.5),
                line=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], width=2),
                customdata=labels,
                hovertemplate="%{customdata}",
            ),
        )

    style_figure(fig, layout={"yaxis_title": "Lines"})

    return fig.to_html()


# FIXME: Add these back in!!
# <table class="striped">
#   <thead>
#     <tr>
#       <th scope="col" style="text-align: left">Metric</th>
#       <th scope="col" style="text-align: center">Value</th>
#       <th scope="col" style="text-align: center">Grade</th>
#       <th scope="col" style="text-align: left"><small>Explanation</small></th>
#     </tr>
#   </thead>
#   <tbody>
#     <tr>
#       <td style="text-align: left">File Density</td>
#       <td style="text-align: center">{{ "{:.0f}".format(cloc_0.row.avg_lines_per_file.score) }}</td>
#       <td style="text-align: center; color: var(--pico-muted-color);
#                  background-color: {{ cloc_0.row.avg_lines_per_file.color }}">
#         {{ cloc_0.row.avg_lines_per_file.grade }}
#       </td>
#       <td style="text-align: left"><small>Average LoC per File</small></td>
#     </tr>
#     <tr>
#       <td style="text-align: left">Code Density</td>
#       <td style="text-align: center">{{ "{:.0f}".format(cloc_0.row.code_density.score) }}%</td>
#       <td style="text-align: center; color: var(--pico-muted-color);
#                  background-color: {{ cloc_0.row.code_density.color }}">
#         {{ cloc_0.row.code_density.grade }}
#       </td>
#       <td style="text-align: left"><small>LOC / (LOC + Blanks)</small></td>
#     </tr>
#     <tr>
#       <td style="text-align: left">Comment Ratio</td>
#       <td style="text-align: center">{{ "{:.0f}".format(cloc_0.row.comment_ratio.score) }}%</td>
#       <td style="text-align: center; color: var(--pico-muted-color);
#                  background-color: {{ cloc_0.row.comment_ratio.color }}">
#         {{ cloc_0.row.comment_ratio.grade }}
#       </td>
#       <td style="text-align: left"><small>Comments / (Comment + LOC)</small></td>
#     </tr>
#   </tbody>
# </table>
