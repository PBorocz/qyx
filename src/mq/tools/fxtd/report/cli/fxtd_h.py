"""..."""

import logging

from mq.cli import cli_console, cli_table
from mq.tools.base import Project
from mq.tools.fxtd import COLORS
from mq.tools.fxtd.models import query
from mq.utils import format_timestamp_headers

log = logging.getLogger(__name__)


def fxtd_h(project: Project) -> None:
    """Report on the history of scans "across"."""
    timestamps, transposed, rocs = query("h", project=project, last=5)
    timestamps_formatted = format_timestamp_headers(timestamps)

    ################################################################################################
    # Render the table
    ################################################################################################
    table = cli_table(title="FXTD Results Over Time")
    table.add_column("-")
    for timestamp in sorted(timestamps):
        table.add_column(timestamps_formatted[timestamp], justify="right")
    table.add_column("Delta")

    for entity_type, values in transposed.items():
        t_row = [entity_type]
        for timestamp in sorted(timestamps):
            t_row.append(f"{values[timestamp]:,d}")

        roc = rocs.get(entity_type, 0)
        if roc > 0.01:
            color = COLORS["positive"]
        elif roc < -0.01:
            color = COLORS["negative"]
        else:
            color = COLORS["neutral"]

        t_row.append(f"[{color}][bold]{roc:+.2f}%[/bold][/{color}]")

        table.add_row(*t_row)

    cli_console.print(table)


#
# Is this still used/valuable?
#
# def _report_history(project: Project) -> None:
#     """Report on the history of scans "across"."""
#     rows, messages, transposed, grand_totals = query("h", project=project, last=5)
#     ################################################################################################
#     # Render the table
#     ################################################################################################
#     table = cli_table(title="FXTD Results Over Time", show_footer=True)
#     table.add_column("Rule", justify="left", footer="TOTAL")
#     table.add_column("Message", justify="left", footer="")
#     timestamps = list({row.timestamp for row in rows})
#     timestamps_formatted = format_timestamp_headers(timestamps)
#     for timestamp in sorted(timestamps):
#         table.add_column(
#             timestamps_formatted[timestamp],
#             justify="right",
#             footer=str(grand_totals[timestamp]),
#             footer_style="bold cyan",
#         )

#     for rule_code, dt_rows in transposed.items():
#         row = [rule_code, messages[rule_code]]
#         for timestamp in sorted(timestamps):
#             row.append(str(dt_rows[timestamp]))
#         table.add_row(*row)

#     cli_console.print(table)
