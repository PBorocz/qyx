"""Master ingest logic."""

import logging
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Callable, Iterator

from rich.console import Console

from mq.tools import generate_ta_pairs
from mq.tools.base import AbstractToolConfiguration, Project, Request, Scan
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

    tools_analyses: list[tuple[AbstractToolConfiguration, str]] = generate_ta_pairs(args)

    for scan_request in iter_scan_requests(args, request):
        for o_tool, analysis in tools_analyses:
            _ingest_analysis(args, request, o_tool, analysis, scan_request)


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    if request.is_git:
        console = Console()
        for repo_path, commit_date, commit_hash in git_commits(request.arg_normalised):
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
            cwd=Path(request.arg_normalised),
            as_of=datetime.now(UTC).replace(microsecond=0),
            hash=get_git_commit_hash(),
        )


def _ingest_analysis(
    args: Namespace,
    request: Request,
    tool_configuration: AbstractToolConfiguration,
    analysis: str,
    scan_request: Namespace,
) -> None:
    """Do the specified analysis for respective tool, running the respective command, parsing and saving results!."""
    # Get the scan (if necessary) on whose behalf the results will be stored.
    if not (scan := _get_ingest_scan(args, request, tool_configuration, analysis, scan_request)):
        return

    ################################################################################################
    # Get the results of running the tool/analysis against the respective state of code!
    ################################################################################################
    datum = _get_ta_results(args, request, tool_configuration, analysis, scan_request)

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
    log.info(f"{scan.as_of_display()} {s_from:10s}: {num:>5,d} results.")


def _get_ingest_scan(
    args: Namespace,
    request: Request,
    tool_configuration: AbstractToolConfiguration,
    analysis: str,
    scan_request: Namespace,
) -> Scan | None:
    """Return the appropriate (usually an new) scan instance."""
    if request.is_git:
        # For git projects, since we REUSE the same request over time,
        # we don't want/need duplicate scans for the same request,
        # tool, analysis and revision:
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
            return None
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

    return scan


def _get_ta_results(
    args: Namespace,
    request: Request,
    tool_configuration: AbstractToolConfiguration,
    analysis: str,
    scan_request: Namespace,
) -> Any:
    """Return the results associated with the tool/analysis, either from stdin or by running the respective tool."""
    if args.stdin:
        ################################################################################################
        # PIPELINE mode - data was run externally and is passed in to us directly via stdin:
        ################################################################################################
        datum: Any = sys.stdin.read()
    else:
        ################################################################################################
        # DIRECT mode - run the tool's command ourselves
        ################################################################################################
        command: list[str] = tool_configuration.get_ingest_command(
            relative=str(request.arg_raw),  # eg. "." usually
            absolute=str(scan_request.cwd),  # eg. /tmp/private... for git or /users/me/projects/myProject for local.
            analysis=analysis,
        )
        log.debug(f"Executing {' '.join(command)=} in {scan_request.cwd}")

        try:
            # log.info(f"{scan_request.as_of=}")
            # log.info(f"{scan_request.hash[:8]=}")
            # log.info(f"{scan_request.cwd=}")
            # log.info(f"{command=}")
            # log.info(f"cwd exists: {scan_request.cwd.exists()}")
            # log.info(
            #     f"cwd contents: {list(scan_request.cwd.iterdir()) if scan_request.cwd.exists() else 'DOES NOT EXIST'}"
            # )
            result = subprocess.run(command, cwd=str(scan_request.cwd), capture_output=True, check=True)
        except subprocess.CalledProcessError as exc:
            log.error(f"{str(exc)}")
            log.error(f"{exc.stdout.decode()=}")
            log.error(f"{exc.stderr.decode()=}")
            log.error(f"{scan_request.as_of=}")
            log.error(f"{scan_request.hash[:8]=}")
            log.error(f"{scan_request.cwd=}")
            log.error(f"{command=}")
            sys.exit(1)

        datum = result.stdout

    return datum
