"""Master ingest logic."""

import json
import logging
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from typing import Iterator

from rich import print

from mq.tools.base import Project, Request, Scan
from mq.tools import save_scan_results, split_arg_tool_analysis
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
    # Lookup (or create) our Project and associated Tequest
    project = Project.create_from_args(args)
    request = Request.create_from_args(args, project)
    ta_pairs = generate_ta_pairs(args)

    for scan_request in iter_scan_requests(args, request):
        log.debug(f"{scan_request=}")
        for o_tool, analysis in ta_pairs:
            _ingest_analysis(args, request, o_tool, analysis, scan_request)


def iter_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    if request.scan_source == "git":
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
    tool_configuration: any,  # FIXME: typing?
    analysis: str,
    scan_request: Namespace,
) -> None:
    scan = Scan.create(
        request=request,
        tool=tool_configuration.module,
        analysis=analysis,
        git_commit_hash=scan_request.hash,
        as_of=scan_request.as_of,  # NOTE: Could be git_revision *OR* "now"
    )

    ################################################################################################
    # Get the tool's data EITHER directly from stdin OR by running it!
    ################################################################################################
    if args.stdin:
        # Pipeline mode - parse JSON from stdin:
        json_ = json.loads(sys.stdin.read())
    else:
        # Direct mode - run the tool's command ourselves
        command = tool_configuration.get_ingest_command(args.project, analysis)
        log.debug(f"{' '.join(command)=}")

        result = subprocess.run(
            command,
            cwd=scan_request.location,
            capture_output=True,
            check=True,
        )
        json_ = json.loads(result.stdout)

    ################################################################################################
    # Parse the results received...
    ################################################################################################
    parse_method = tool_configuration.get_parse_method(analysis)
    results = parse_method(json_)

    ################################################################################################
    # Save em'!
    ################################################################################################
    num = save_scan_results(scan, results)

    s_from = tool_configuration.module
    if tool_configuration.module != analysis:
        s_from += f":{analysis}"
    print(f"[green]✓ Ingested [bold]{num:3d}[/bold] results from {s_from}[/green] as of {scan.as_of_display()}")


def generate_ta_pairs(args: Namespace) -> list[tuple[str, str]]:
    """Process the command-line argument and return a list of Tools and analyses to perform."""
    ################################################################################
    # Case 1: tool_analysis is empty -> we want to ingest everything!
    ################################################################################
    return_ = list()
    if not args.tool_analysis:
        for tool_name in args.tools.keys():
            tool_configuration = args.tools[tool_name]
            for analysis_name in tool_configuration.analyses:
                return_.append((tool_configuration, analysis_name))
        return return_

    arg_tool, arg_analysis = split_arg_tool_analysis(args.tool_analysis)

    ################################################################################
    # Case 2: Tool only, give all the analyses the tool supports
    ################################################################################
    if not arg_analysis:
        tool_configuration = args.tools[arg_tool]
        for analysis_name in tool_configuration.analyses:
            return_.append((tool_configuration, analysis_name))
        return return_

    ################################################################################
    # Case 3: Tool and Analysis specified
    ################################################################################
    assert arg_tool and arg_analysis
    return [(args.tools[arg_tool], arg_analysis)]
