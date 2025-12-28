"""Master ingest logic."""

import json
import logging
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from typing import Callable, Iterator

from rich import print

from mq.tools import generate_ta_pairs, save_scan_results, AbstractModuleConfiguration
from mq.tools.base import Project, Request, Scan
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
    request: Request = Request.create_from_args(args, project)

    tools_analyses: list[tuple[AbstractModuleConfiguration, str]] = generate_ta_pairs(args)

    for scan_request in iter_scan_requests(args, request):
        log.debug(f"{scan_request=}")
        for o_tool, analysis in tools_analyses:
            _ingest_analysis(args, request, o_tool, analysis, scan_request)


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    if request.from_git():
        for repo_path, commit_date, commit_hash in git_commits(args):
            yield Namespace(
                as_git=True,
                location=repo_path,
                as_of=commit_date,
                hash=commit_hash,
            )
    else:
        yield Namespace(
            as_git=False,
            location=args.project,
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
    scan: Scan = Scan.create(
        request=request,
        tool=tool_configuration.module_name,
        analysis=analysis,
        git_commit_hash=scan_request.hash,
        as_of=scan_request.as_of,  # NOTE: Could be git_revision *OR* "now"
    )

    ################################################################################################
    # Get the tool's data EITHER directly from stdin OR by running it!
    ################################################################################################
    if args.stdin:
        # Pipeline mode - parse JSON from stdin:
        json_: list | dict = json.loads(sys.stdin.read())
    else:
        # Direct mode - run the tool's command ourselves
        command: list[str] = tool_configuration.get_ingest_command(args.project, analysis)
        log.debug(f"Executing {' '.join(command)=} in {scan_request.location}")

        result = subprocess.run(
            command,
            cwd=scan_request.location,
            capture_output=True,
            check=True,
        )
        json_: list | dict = json.loads(result.stdout)

    ################################################################################################
    # Parse the results received...
    ################################################################################################
    parse_method: Callable = tool_configuration.get_parse_method(analysis)
    results: list = parse_method(json_)

    ################################################################################################
    # Save em'!
    ################################################################################################
    num: int = save_scan_results(scan, results)

    s_from: str = tool_configuration.module_name
    if tool_configuration.module_name != analysis:
        s_from += f":{analysis}"
    print(f"[green]✓ Ingested [bold]{num:3d}[/bold] results from {s_from}[/green] as of {scan.as_of_display()}")
