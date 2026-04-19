"""Master ingest (ie. run, parse/save) logic."""

import logging
import shlex
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from pathlib import Path
from platformdirs import user_log_dir
from subprocess import CalledProcessError
from types import SimpleNamespace as Sns
from typing import Any, Callable, Iterator

from peewee import IntegrityError
from rich.console import Console

from qyx.constants import ALL_ITEMS
from qyx.tools._models_ import ToolDimension, ToolType, Project, Request, Scan
from qyx.utils.git import git_checkout, get_git_commits, git_goto_head

log = logging.getLogger(__name__)

console = Console()

first_for_scan: bool = None


def ingest(args: Namespace) -> None:
    """Ingest from the specified tool, either current or from git."""
    global first_for_scan
    # Lookup (or create) our Project and associated Request
    o_project: Project = Project.factory(args)
    o_request: Request = Request.get_or_create(args, o_project)

    # Generate the tools we should evaluate.
    tools: list[ToolType] = _get_tools_from_args(args)
    args.log_file: Path = _setup_error_logging()

    for scan_request in _get_scan_requests(args, o_request):
        first_for_scan = True
        printed: list[bool] = []
        for o_tool in tools:
            # Some tools aren't meant to process "history" as they do so themselves (eg. ga)
            if o_tool.ingest_latest_only and not scan_request.latest:
                continue

            if scan_request.as_git:
                git_checkout(scan_request)

            ################################################################################
            # CORE!!: Do the respective tool's ingestion and save the activity it did.
            ################################################################################
            printed.append(_do_scan(args, o_request, o_tool, scan_request))

        if any(printed):
            console.print()
            console.file.flush()

    # Always leave a git-sourced project in a "HEAD" state
    if scan_request.as_git:
        git_goto_head(o_request.arg_normalised)


def _setup_error_logging() -> Path:
    """Setup log directory for subprocess issues."""
    log_path = Path(user_log_dir("qyx"))
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{timestamp}.log"

    return log_file


def _get_tools_from_args(args: Namespace) -> list[ToolType]:
    """Process the command-line or interactive arguments and return a list of tool(s) to perform an ingest upon."""
    # Case 1: No tool specified -> we want to "ingest" everything!
    if not args.tool or args.tool == ALL_ITEMS:
        return args.tools.tools()

    # Case 2: Lookup the specific tool by name.
    try:
        return [args.tools[args.tool.lower()]]
    except KeyError:
        raise RuntimeError(f"Sorry, unable to find {args.tool.lower()}!")


def _get_scan_requests(args: Namespace, o_request: Request) -> Iterator[Sns]:
    """Iterate over ingest request(s) to perform, abstracting out git vs. direct file sources."""
    #
    # Fundamentally, the only difference between pulling from git versus from the current status
    # on disk is (a) the location and (b) the "as-of" date associated with the state of the code
    # when the tool runs.
    #
    if o_request.is_git:
        repo_path, commits = get_git_commits(o_request.arg_normalised)
        for commit in commits:
            s_as_of = f"{commit.utc_date.strftime('%Y-%m-%dT%H:%M:%S')}"
            yield Sns(
                as_git=True,
                cwd=repo_path,
                as_of=commit.utc_date,
                s_as_of=s_as_of,
                hash=commit.hash_val,
                message=commit.message,
                latest=commit.latest,
            )
    else:
        as_of = datetime.now(UTC).replace(microsecond=0)
        s_as_of = f"{as_of.strftime('%Y-%m-%dT%H:%M:%S')}"
        yield Sns(
            as_git=False,
            cwd=Path(o_request.arg_normalised),
            as_of=as_of,
            s_as_of=s_as_of,
            hash=None,
            message=None,
            latest=True,  # ALWAYS True when we're getting from the file system!
        )


def _do_scan(
    args: Namespace,
    o_request: Request,
    o_tool: ToolType,
    scan_request: Sns,
) -> bool:
    """Ingest a tool: run the respective command(s), parse and save results!."""
    global first_for_scan

    dimensions_to_ingest: list[ToolDimension | None] = o_tool.dimensions if o_tool.ingest_by_dimension else [None]

    printed = False
    for dimension in dimensions_to_ingest:
        parse_method: Callable = o_tool.get_parse_save_method(dimension)
        assert parse_method, f"Sorry, we couldn't find a parse/ingest method for {dimension=} obo {o_tool.name=}"

        if dimension:
            # Running multiple ingest commands for the tool, one for each possible dimension.
            ingest_dimension = dimension.name
            tool_dim = f"{o_tool.name}-{dimension.name}"
        else:
            # Running a single command for the entire tool (irrespective of *REPORTING* dimensions)
            ingest_dimension = o_tool.name
            tool_dim = o_tool.name

        try:
            # Create the scan on whose behalf the results will be stored.
            scan = Scan.create(
                request=o_request,
                tool=o_tool.name,
                ingest_dimension=ingest_dimension,
                cwd=scan_request.cwd,
                git_commit_hash=scan_request.hash,
                git_commit_message=scan_request.message,
                as_of=scan_request.as_of,
            )
        except IntegrityError:
            continue

        ################################################################################################
        # Run the respective tool's data collection method...
        ################################################################################################
        datum, error = _run_tool(args, o_request, o_tool, scan_request, dimension)
        if error:
            # We ran into a problem with running the ingest, don't leave the scan hanging around
            scan.delete_instance(recursive=True)  # recursive is just in case..
            if first_for_scan:
                console.print(f"{scan_request.s_as_of} - Ingested", end="")
                first_for_scan = False
            console.print(f" [red]{tool_dim}:❌[/red]", end="")
            printed = True
            continue

        ################################################################################################
        # Parse & save the results received this time using the respective tool's ingest method
        ################################################################################################
        result_count: int = parse_method(scan, scan_request.latest, datum)
        s_result_count = f"{result_count:,d}" if result_count else "✔"
        if first_for_scan:
            console.print(f"{scan_request.s_as_of} - Ingested", end="")
            first_for_scan = False
            printed = True
        console.print(f" [green]{tool_dim}:{s_result_count}[/green]", end="")

    return printed


def _run_tool(
    args: Namespace,
    o_request: Request,
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
            # "." usually
            relative=str(o_request.arg_raw),
            # eg. <user_cache_dir>/qyx/repos/. for git or /users/me/projects/myProject for local.
            absolute=str(scan_request.cwd),
            dimension=dimension,
        )

        log.debug(f"Executing {scan_request.cwd=}")
        log.debug(f"Executing {shlex.join(command)=}")
        try:
            result = subprocess.run(
                command,
                cwd=str(scan_request.cwd),
                capture_output=True,
                check=True,
                text=True,
            )
        except CalledProcessError as exc:
            _write_error_log(args.log_file, scan_request, command, exc)
            return None, True

        datum = result.stdout

    return datum, False


def _write_error_log(log_file: Path, scan_request: Sns, command: list[str], exc: CalledProcessError):
    with open(log_file, "a") as fh_:
        fh_.write("=" * 80 + "\n")
        fh_.write(f"Command           : {shlex.join(command)}\n")
        fh_.write(f"Working Directory : {scan_request.cwd}\n")
        fh_.write(f"Return Code       : {exc.returncode}\n")
        fh_.write(f"As Of             : {scan_request.as_of}\n")
        if scan_request.as_git:
            fh_.write(f"Git hash          : {scan_request.hash}\n")
            fh_.write(f"Git message       : {scan_request.message}\n")

        if exc.stdout:
            fh_.write("\n" + "-" * 80 + "\n")
            fh_.write("STDOUT:\n")
            fh_.write("-" * 80 + "\n")
            fh_.write(exc.stdout)

        if exc.stderr:
            fh_.write("\n" + "-" * 80 + "\n")
            fh_.write("STDERR:\n")
            fh_.write("-" * 80 + "\n")
            fh_.write(exc.stderr)
        fh_.write("\n")
