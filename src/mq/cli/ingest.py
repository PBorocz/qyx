"""Master ingest logic."""

import logging
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from typing import Any, Callable, Iterator

from rich.console import Console

from mq.tools import generate_ta_pairs
from mq.tools.base import AbstractModuleConfiguration, Project, Request, Scan
from mq.utils.git import get_git_commit_hash, git_commits

log = logging.getLogger(__name__)


def ingest(args: Namespace) -> None:
    """Ingest from the specified tool, either current or from git."""
    #
    # Fundamentally, the only difference between pulling from git vs.
    # from the current status on disk is (a) the location and (b) the
    # "as-of" date associated with the state of the code when the tool
    # runs.
    #
    # Lookup (or create) our Project and associated Request
    project: Project = Project.create_from_args(args)
    request: Request = Request.get_or_create(args, project)

    tools_analyses: list[tuple[AbstractModuleConfiguration, str]] = generate_ta_pairs(args)

    for scan_request in iter_scan_requests(args, request):
        for o_tool, analysis in tools_analyses:
            _ingest_analysis(args, request, o_tool, analysis, scan_request)


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    if request.from_git():
        console = Console()
        for repo_path, commit_date, commit_hash in git_commits(args):
            console.print(f"[bold cyan]Processing...[/] {commit_date.strftime('%Y-%m-%dT%H:%M:%S')}", end="\r")
            yield Namespace(
                as_git=True,
                cwd=repo_path,
                as_of=commit_date,
                hash=commit_hash,
            )
        console.print("\n[bold green]✓ Done![/]")
    else:
        yield Namespace(
            as_git=False,
            cwd=args.project,
            as_of=datetime.now(UTC),
            hash=get_git_commit_hash(),
        )


def _ingest_analysis(
    args: Namespace,
    request: Request,
    tool_configuration: AbstractModuleConfiguration,
    analysis: str,
    scan_request: Namespace,
) -> None:
    if args.git:
        ################################################################################################
        # Have we already done this scan? If so, save to skip...
        ################################################################################################
        try:
            scan = (
                Scan.select()
                .where(
                    Scan.request == request,
                    Scan.tool == tool_configuration.module_name,
                    Scan.analysis == analysis,
                    Scan.git_commit_hash == scan_request.hash,
                )
                .get()
            )
            log.debug(
                f"Skipping...we've already scanned {scan.tool}:{scan.analysis} "
                f"as of: {scan.as_of} obo {scan.git_commit_hash[:8]}",
            )
            return
        except Scan.DoesNotExist:
            ...

    scan: Scan = Scan.create(
        request=request,
        tool=tool_configuration.module_name,
        analysis=analysis,
        cwd=scan_request.cwd,
        git_commit_hash=scan_request.hash,
        as_of=scan_request.as_of,  # NOTE: Could be git_revision *OR* "now"
    )

    ################################################################################################
    # Get the tool's data EITHER directly from stdin OR by running it!
    ################################################################################################
    if args.stdin:
        # Pipeline mode - get from stdin:
        datum: Any = sys.stdin.read()
    else:
        # Direct mode - run the tool's command ourselves
        command: list[str] = tool_configuration.get_ingest_command(args.project, analysis)
        log.debug(f"Executing {' '.join(command)=} in {scan_request.cwd}")

        result = subprocess.run(command, cwd=scan_request.cwd, capture_output=True, check=True)
        datum = result.stdout

    ################################################################################################
    # Parse & save the results received...
    ################################################################################################
    ingest_method: Callable = tool_configuration.get_ingest_method(analysis)
    num: int = ingest_method(scan, datum)

    ################################################################################################
    # Report status
    ################################################################################################
    s_from: str = tool_configuration.module_name
    if tool_configuration.module_name != analysis:
        s_from += f":{analysis}"
    # from rich import print
    # print(f"[green]✓ Ingested [bold]{num:3d}[/bold] results from {s_from}[/green] as of {scan.as_of_display()}")
    log.info(f"Ingested {num:>5,d} results from {s_from:10s} as of {scan.as_of_display()}")
