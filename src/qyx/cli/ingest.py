"""Master ingest (ie. run, parse/save) logic."""

import logging
import shlex
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace as Sns
from typing import Any, Callable, Iterator

from peewee import IntegrityError
from rich import print as rprint

from qyx.constants import ALL_ITEMS
from qyx.tools._models_ import ToolDimension, ToolType, Project, Request, Scan
from qyx.utils.git import git_checkout, get_git_commits

log = logging.getLogger(__name__)


def ingest(args: Namespace) -> None:
    """Ingest from the specified tool, either current or from git."""
    # Lookup (or create) our Project and associated Request
    project: Project = Project.factory(args)
    request: Request = Request.get_or_create(args, project)

    # Generate the tools we should evaluate.
    tools: list[ToolType] = _get_tools_from_args(args)

    for scan_request in _get_scan_requests(args, request):
        for o_tool in tools:
            if scan_request.as_git:
                git_checkout(scan_request)
            # Do the respective tool's ingestion
            _do_scan(args, request, o_tool, scan_request)


################################################################################################
def _get_tools_from_args(args: Namespace) -> list[ToolType]:
    """Process the command-line or interactive arguments and return a list of tool(s) to perform an ingest upon."""
    # Case 1: No tool specified -> we want to "ingest" everything!
    if not args.tool or args.tool == ALL_ITEMS:
        return args.tools.values()

    # Case 2: Lookup the specific tool by name.
    try:
        return [args.tools[args.tool.lower()]]
    except KeyError:
        raise RuntimeError(f"Sorry, unable to find {args.tool.lower()}!")


def _get_scan_requests(args: Namespace, request: Request) -> Iterator[Sns]:
    """Iterate over ingest request(s) to perform, abstracting out git vs. direct file sources."""
    #
    # Fundamentally, the only difference between pulling from git
    # versus from the current status on disk is (a) the location and
    # (b) the "as-of" date associated with the state of the code when
    # the tool runs.
    #
    if request.is_git:
        repo_path, commits = get_git_commits(request.arg_normalised)
        for commit in commits:
            s_as_of = f"{commit.utc_date.strftime('%Y-%m-%dT%H:%M:%S')}"
            yield Sns(
                as_git=True,
                cwd=repo_path,
                as_of=commit.utc_date,
                s_as_of=s_as_of,
                hash=commit.hash_val,
                message=commit.message,
            )
    else:
        as_of = datetime.now(UTC).replace(microsecond=0)
        s_as_of = f"{as_of.strftime('%Y-%m-%dT%H:%M:%S')}"
        yield Sns(
            as_git=False,
            cwd=Path(request.arg_normalised),
            as_of=as_of,
            s_as_of=s_as_of,
            hash=None,
            message=None,
        )


def _do_scan(args: Namespace, request: Request, o_tool: ToolType, scan_request: Sns) -> tuple[int, bool]:
    """Ingest a tool: run the respective command(s), parse and save results!."""
    dimensions_to_ingest: list[ToolDimension | None] = o_tool.dimensions if o_tool.ingest_by_dimension else [None]
    for dimension in dimensions_to_ingest:
        if dimension:
            # Running multiple ingest commands for the tool, one for each possible dimension.
            ingest_dimension = dimension.name
            display = f"{o_tool.name}:{dimension.name}"
        else:
            # Running a single command for the entire tool (irrespective of *REPORTING* dimensions)
            ingest_dimension = o_tool.name
            display = o_tool.name
        try:
            # Create the scan on whose behalf the results will be stored.
            scan = Scan.create(
                request=request,
                tool=o_tool.name,
                ingest_dimension=ingest_dimension,
                cwd=scan_request.cwd,
                git_commit_hash=scan_request.hash,
                git_commit_message=scan_request.message,
                as_of=scan_request.as_of,
            )
        except IntegrityError:
            if log.isEnabledFor(logging.DEBUG):
                rprint(f"[yellow]⚠ {scan_request.s_as_of} - Scan already exists for {display}[/yellow]")
            continue

        ################################################################################################
        # Run the respective tool's data collection method...
        ################################################################################################
        datum, error = _run_tool(args, request, o_tool, scan_request, dimension)
        if error:
            # We ran into a problem with running the ingest, don't leave the scan hanging around
            scan.delete_instance(recursive=True)  # recursive is just in case..
            rprint(f"[red]❌ {scan_request.s_as_of} - Unable to ingest from {display}[/red]")
            return

        ################################################################################################
        # Parse & save the results received this time using the respective tool's ingest method
        ################################################################################################
        parse_method: Callable = o_tool.get_parse_method(dimension)
        result_count: int = parse_method(scan, datum)
        rprint(
            f"[green]✔ {scan_request.s_as_of} - Ingested [bold]{result_count:3d}[/bold] from {display}[/green]",
        )


def _run_tool(
    args: Namespace,
    request: Request,
    o_tool: ToolType,
    scan_request: Sns,
    dimension: ToolDimension = None,
) -> tuple[Any, bool]:
    """Return the results associated with the tool (dimension), either from stdin or by running the respective tool."""
    if args.stdin:
        ################################################################################################
        # PIPELINE mode - data was run externally and is passed in to us directly via stdin:
        ################################################################################################
        datum: Any = sys.stdin.read()
    else:
        ################################################################################################
        # DIRECT mode - run the tool's command ourselves
        ################################################################################################
        command: list[str] = o_tool.get_ingest_command(
            args,
            relative=str(request.arg_raw),  # eg. "." usually
            absolute=str(scan_request.cwd),  # eg. /tmp/private... for git or /users/me/projects/myProject for local.
            dimension=dimension,
        )

        log.debug(f"Executing {scan_request.cwd=}")
        log.debug(f"Executing {shlex.join(command)=}")
        try:
            result = subprocess.run(command, cwd=str(scan_request.cwd), capture_output=True, check=True)
        except subprocess.CalledProcessError as exc:
            for line in exc.stdout.decode().split("\n"):
                if line:
                    log.debug(f"STDOUT: {line}")
            for line in exc.stderr.decode().split("\n"):
                if line:
                    log.debug(f"STDERR: {line}")
            log.debug(f"{scan_request.as_of=}")
            log.debug(f"{scan_request.cwd=}")
            log.debug(f"{shlex.join(command)=}")
            return None, True

        datum = result.stdout

    return datum, False
