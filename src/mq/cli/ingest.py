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
    if args.git:
        ...
        # parse_git(args)
    else:
        if args.module:
            # Single ingest request, lookup the method and do it!
            parse_single(args)
        else:
            # Ingest over ALL available modules..
            for module in MODULE_NAMES:
                args.module = module
                parse_single(module)


################################################################################################
# Generic non-git ingestion
################################################################################################
def parse_single(args: Namespace) -> None:
    # Lookup the py_module based on the args.module were working on
    py_module = MODULES_AND_MODELS[args.module]["module"]

    # Use this to find module's json parse method
    py_parse = import_module(".parse", package=py_module.__name__)
    method_parse = getattr(py_parse, "parse_json")  # Ok to go directly to AttributeError.

    project = Project.create_from_args(args)

    request = Request.create_from_args(args, project)

    git_commit_hash = get_git_commit_hash()
    scan = Scan.create(request=request, module=args.module.lower(), git_commit_hash=git_commit_hash)

    if args.stdin:
        # Pipeline mode - parse JSON from stdin:
        data = json.loads(sys.stdin.read())
    else:
        # Direct mode - run the module's command ourselves:
        command = py_module.INGEST_ARGS
        command.extend([args.project])
        log.debug(f"{' '.join(command)=}")

        result = subprocess.run(command, capture_output=True, check=True)
        data = json.loads(result.stdout)

    # Parse and save the results!
    results = method_parse(data)
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
