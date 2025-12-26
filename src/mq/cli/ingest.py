"""."""

import json
import logging
import subprocess
import sys
from argparse import Namespace
from importlib import import_module

from rich import print

from mq.cli import get_method
from mq.modules.base import Project, Request, Scan
from mq.modules import MODULE_NAMES, MODULES_AND_MODELS
from mq.modules import save_scan_results
from mq.utils.git import get_git_commit_hash

log = logging.getLogger(__name__)


def ingest(args: Namespace) -> None:
    # Lookup (or create) our project!
    project = Project.create_from_args(args)

    # Store info obo the request
    request = Request.create_from_args(args, project)
    if args.git:
        ...
        # parse_git(args, project, request)
    else:
        if args.module:
            # Single ingest request for a particular module.
            parse_single(args, project, request)
        else:
            # Ingest over ALL available modules..
            for module in MODULE_NAMES:
                args.module = module
                parse_single(module, project, request)


################################################################################################
# Generic non-git ingestion
################################################################################################
def parse_single(args: Namespace, project: Project, request: Request) -> None:
    """Capture information for the specified module (ie. run, parse and store)."""
    # Lookup the py_module based on the args.module were working on
    py_module = MODULES_AND_MODELS[args.module]["module"]

    sub_module = args.sub_module.lower() if args.sub_module else None
    scan = Scan.create(
        request=request,
        module=args.module.lower(),
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
        # Direct mode - run the module's command ourselves:
        command = py_module.get_ingest_command(args.project, args.sub_module)
        log.debug(f"{' '.join(command)=}")

        result = subprocess.run(command, capture_output=True, check=True)
        json_ = json.loads(result.stdout)

    ################################################################################################
    # Parse the results received...
    ################################################################################################
    # Find either the module's json parse method or one specific to the sub_module
    py_parse = import_module(".parse", package=py_module.__name__)  # eg. .../<module>/parse.py
    parse_method_name = py_module.get_parse_method_name(args.sub_module)  # eg.  "parse_json" or "parse_json_cc"
    log.debug(f"{parse_method_name=}")
    parse_method = getattr(py_parse, parse_method_name)  # eg. parse_json()
    log.debug(f"{parse_method=}")
    results = parse_method(json_)

    ################################################################################################
    # Save em'!
    ################################################################################################
    num = save_scan_results(scan, results)
    print(f"[green]✓ Ingested [bold]{num}[/bold] results from {args.module.upper()}[/green]")


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
