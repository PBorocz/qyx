"""Master ingest (ie. run, parse/save) logic."""

import logging
import subprocess
import sys
from argparse import Namespace
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace as Sns
from typing import Any, Callable, Iterator

from rich import print as rprint

from qyx.tools import generate_ta_pairs
from qyx.tools.base import ToolType, Project, Request, Scan
from qyx.utils.git import git_checkout, get_git_commits

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
    project: Project = Project.factory(args)
    request: Request = Request.get_or_create(args, project)

    # Gather all the git hash keys we've already processed for this request (if any)
    git_hashes: dict[tuple[str, str]] = _get_git_hashes(request)  # Key: (tool, analysis)

    # Generate the combination of tools and respective analyses we should evaluate.
    tools_analyses: list[tuple[ToolType, str]] = generate_ta_pairs(args)

    ingestion_count = 0
    for scan_request in iter_scan_requests(args, request):
        s_as_of = f"{scan_request.as_of.strftime('%Y-%m-%dT%H:%M:%S')}"

        for o_tool, analysis in tools_analyses:
            if scan_request.as_git:
                # If we're scanning a git repo, check to make sure we haven't already ingested this hash!
                if _is_git_commit_already_ingested(git_hashes, o_tool, analysis, scan_request.hash):
                    log.debug(f"{o_tool.name}:{analysis} - {scan_request.hash[:8]=} already done!")
                    continue

                # We haven't! put the repo into the right git state for ingestion
                git_checkout(scan_request)

            ################################################################################
            # Do the respective tool's ingestion
            ################################################################################
            s_as_of = f"{scan_request.as_of.strftime('%Y-%m-%dT%H:%M:%S')}"
            s_analysis = analysis if o_tool.name != analysis else ""
            rprint(f"{s_as_of} → {o_tool.name} {s_analysis}...", end="\r")

            num = _ingest_analysis(args, request, o_tool, analysis, scan_request)

            display: str = o_tool.name if o_tool.name == analysis else f"{o_tool.name}:{analysis}"
            rprint(f"[green]✔ Ingested [bold]{num:3d}[/bold] results on behalf of {display}[/green]")
            ingestion_count += 1

    if not ingestion_count:
        rprint("[cyan]Nothing done![/cyan]")


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Sns]:
    """Iterate over ingest request(s) to perform, abstracting out git vs. direct file sources."""
    if request.is_git:
        repo_path, commits = get_git_commits(request.arg_normalised)
        for commit in commits:
            yield Sns(as_git=True, cwd=repo_path, as_of=commit.utc_date, hash=commit.hash_val, message=commit.message)
    else:
        as_of = datetime.now(UTC).replace(microsecond=0)
        yield Sns(as_git=False, cwd=Path(request.arg_normalised), as_of=as_of, hash=None, message=None)


def _ingest_analysis(
    args: Namespace,
    request: Request,
    o_tool: ToolType,
    analysis: str,
    scan_request: Sns,
) -> int:
    """Do the specified analysis for respective tool, running the respective command, parsing and saving results!."""
    # Create the scan on whose behalf the results will be stored.
    scan = Scan.create(
        request=request,
        tool=o_tool.name,
        analysis=analysis,
        cwd=scan_request.cwd,
        git_commit_hash=scan_request.hash,
        git_commit_message=scan_request.message,
        as_of=scan_request.as_of,
    )

    ################################################################################################
    # Run the respective tool's data collection method...
    ################################################################################################
    datum = _run_tool(args, request, o_tool, analysis, scan_request)

    ################################################################################################
    # Parse & save the results received this time using the respective tool's ingest method
    ################################################################################################
    parse_method: Callable = o_tool.get_parse_method(analysis)
    return parse_method(scan, datum)


def _run_tool(
    args: Namespace,
    request: Request,
    o_tool: ToolType,
    analysis: str,
    scan_request: Sns,
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
        command: list[str] = o_tool.get_ingest_command(
            args,
            relative=str(request.arg_raw),  # eg. "." usually
            absolute=str(scan_request.cwd),  # eg. /tmp/private... for git or /users/me/projects/myProject for local.
            analysis=analysis,
        )
        import shlex

        log.debug(f"Executing from: {scan_request.cwd=}")
        log.debug(f"Executing cmd:  {shlex.join(command)=}")
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
            log.error(f"{len(exc.stdout.decode())=}")
            log.error(f"{exc.stderr.decode()=}")
            log.error(f"{scan_request.as_of=}")
            log.error(f"{scan_request.cwd=}")
            log.error(f"{command=}")
            sys.exit(1)

        datum = result.stdout

    return datum


def _get_git_hashes(request: Request) -> dict[tuple[str, str], str]:
    """Return the git hashes already performed for each tool/analysis combination."""
    return_ = defaultdict(list)
    for row in Scan.select().where(Scan.request == request):
        return_[(row.tool, row.analysis)].append(row.git_commit_hash)
    return dict(return_)


def _is_git_commit_already_ingested(
    git_hashes: dict[tuple[str, str], str],
    o_tool: ToolType,
    analysis: str,
    git_hash: str,
) -> bool:
    """Have we already processed a scan for this tool/analysis based on the git commit hash provided?"""
    if hashes_for_ta := git_hashes.get((o_tool.name, analysis), None):
        return git_hash in hashes_for_ta
    return False
