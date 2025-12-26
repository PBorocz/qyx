"""."""

import json
import logging
import subprocess
import sys
from argparse import Namespace

from rich import print

from mq.modules.base import Project, Request, Scan
from mq.modules import save_scan_results
from mq.utils.git import get_git_commit_hash

log = logging.getLogger(__name__)


def ingest(args: Namespace) -> None:
    # Lookup (or create) our project!
    project = Project.create_from_args(args)

    # Store info obo the request
    request = Request.create_from_args(args, project)
    if args.git:
        # Doing a "history" run, ie. overall git revisions over time.
        ...
        # parse_git(args, project, request)
    else:
        # Doing a "current" run, ie. as of this moment.
        for module in args.MODULES.keys():
            if args.module and args.module.lower() != module.lower():
                continue
            parse_module(args, module, request)


################################################################################################
# Generic non-git ingestion
################################################################################################
def parse_module(args: Namespace, module: str, request: Request) -> None:
    """Capture information for the specified module (ie. run, parse and store)."""
    # Lookup the module's configuration instance based on the module specified
    configuration = args.MODULES[module]
    log.debug(f"{configuration}")

    for sub_module in configuration.sub_modules:
        if args.sub_module and args.sub_module.lower() != sub_module.lower():
            continue
        parse_sub_module(args, request, configuration, module, sub_module)


def parse_sub_module(args: Namespace, request: Request, configuration, module: str, sub_module: str) -> None:
    scan = Scan.create(
        request=request,
        module=module.lower(),
        sub_module=sub_module,
        git_commit_hash=get_git_commit_hash(),
    )

    ################################################################################################
    # Get the tool's data EITHER directly from stdin OR by running it!
    ################################################################################################
    if args.stdin:
        # Pipeline mode - parse JSON from stdin:
        json_ = json.loads(sys.stdin.read())
    else:
        # Direct mode - run the module's command ourselves
        command = configuration.get_ingest_command(args.project, sub_module)
        log.debug(f"{' '.join(command)=}")

        result = subprocess.run(command, capture_output=True, check=True)
        json_ = json.loads(result.stdout)

    ################################################################################################
    # Parse the results received...
    ################################################################################################
    parse_method = configuration.get_parse_method(sub_module)
    results = parse_method(json_)

    ################################################################################################
    # Save em'!
    ################################################################################################
    num = save_scan_results(scan, results)

    s_from = module.upper()
    if module.upper() != sub_module.upper():
        s_from += f"-{sub_module.upper()}"
    print(f"[green]✓ Ingested [bold]{num}[/bold] results from {s_from}[/green]")


# def ingest(args: Namespace) -> None:
#     if args.module:
#         # Single ingest request, lookup the method and do it!
#         __do_ingest(args)
#     else:
#         # Ingest over ALL available modules..
#         for module in MODULE_NAMES:
#             __do_ingest(module)


# def __do_ingest(args: Namespace) -> None:
#     method, msg = get_method(args.module, "ingest", "ingest")
#     if not method and msg:
#         logging.error(msg)
#         return sys.exit(1)
#     method(args)
