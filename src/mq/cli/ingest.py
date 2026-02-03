"""Master ingest logic."""

import logging
import subprocess
import sys
from argparse import Namespace
from collections import defaultdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Callable, Iterator

from rich import print as rprint

from mq.tools import generate_ta_pairs
from mq.tools.base import ToolType, Project, Request, Scan
from mq.utils.git import get_git_commit_hash, git_checkout, get_git_commits

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

    # Gather all the git hash keys we've already processed for this request (if any)
    git_hashes: dict[tuple[str, str]] = _get_git_hashes(request)  # Key: (tool, analysis)

    # Generate the combination of tools and respective analyses we should evaluate.
    tools_analyses: list[tuple[ToolType, str]] = generate_ta_pairs(args)

    ingestion_count = 0
    for scan_request in iter_scan_requests(args, request):
        s_as_of = f"{scan_request.as_of.strftime('%Y-%m-%dT%H:%M:%S')}"

        for o_tool, analysis in tools_analyses:
            s_tool_analysis: str = o_tool.name
            if o_tool.name != analysis:
                s_tool_analysis += f":{analysis}"

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
            rprint(f"[green]✔ Ingested [bold]{num:3d}[/bold] results on behalf of {s_tool_analysis}[/green]")
            ingestion_count += 1

    if not ingestion_count:
        rprint("[cyan]Nothing done![/cyan]")


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    """Iterate over ingest request(s) to perform, abstracting out git vs. direct file sources."""
    if request.is_git:
        repo_path, commits = get_git_commits(request.arg_normalised)
        for commit_hash, commit_date in commits:
            yield Namespace(as_git=True, cwd=repo_path, as_of=commit_date, hash=commit_hash)
    else:
        as_of = datetime.now(UTC).replace(microsecond=0)
        yield Namespace(as_git=False, cwd=Path(request.arg_normalised), as_of=as_of, hash=get_git_commit_hash())


def _ingest_analysis(
    args: Namespace,
    request: Request,
    o_tool: ToolType,
    analysis: str,
    scan_request: Namespace,
) -> int:
    """Do the specified analysis for respective tool, running the respective command, parsing and saving results!."""
    # Get the scan (if necessary) on whose behalf the results will be stored.
    scan = Scan.create(
        request=request,
        tool=o_tool.name,
        analysis=analysis,
        cwd=scan_request.cwd,
        git_commit_hash=scan_request.hash,
        as_of=scan_request.as_of,
    )

    ################################################################################################
    # Run the respective tool's data collection method...
    ################################################################################################
    datum = _get_ta_results(args, request, o_tool, analysis, scan_request)

    ################################################################################################
    # Parse & save the results received this time using the respective tool's ingest method
    ################################################################################################
    ingest_method: Callable = o_tool.get_ingest_method(analysis)
    return ingest_method(scan, datum)


def _get_ta_results(
    args: Namespace,
    request: Request,
    o_tool: ToolType,
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
        command: list[str] = o_tool.get_ingest_command(
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


def _get_git_hashes(request: Request) -> dict:
    """Return the git hashes already performed for each tool/analysis combination."""
    return_ = defaultdict(list)
    for row in Scan.select().where(Scan.request == request):
        return_[(row.tool, row.analysis)].append(row.git_commit_hash)
    count = sum(len(hashes) for hashes in return_.values())
    log.debug(f"Read {count:,d} git hashes for request '{request.arg_normalised}' [{request.id}]")
    return dict(return_)


def _is_git_commit_already_ingested(
    git_hashes: dict,
    o_tool: ToolType,
    analysis: str,
    git_hash: str,
) -> bool:
    """Have we already processed a scan for this tool/analysis based on the git commit hash provided?"""
    if hashes_for_ta := git_hashes.get((o_tool.name, analysis), None):
        return git_hash in hashes_for_ta
    return False
