"""Master ingest logic."""

import json
import logging
import subprocess
import sys
from argparse import Namespace
from datetime import datetime, UTC
from typing import Iterator

from rich import print

from mq.modules.base import Project, Request, Scan
from mq.modules import save_scan_results
from mq.utils.git import extract_repo_name, get_git_commit_hash, git_commits

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

    for scan_request in generate_scan_requests(args, request):
        log.debug(f"{scan_request=}")
        _ingest_scan_request(args, project, request, scan_request)
    return


def generate_scan_requests(args: Namespace, request: Request) -> Iterator[Namespace]:
    if request.scan_source == "git":
        repo_name = extract_repo_name(args.git)
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


def _ingest_scan_request(args: Namespace, project: Project, request: Request, scan_request: Namespace) -> None:
    for module in args.modules.keys():
        if args.module and args.module.lower() != module.lower():
            continue
        _ingest_module(args, module.lower(), request, scan_request)


def _ingest_module(args: Namespace, module: str, request: Request, scan_request: Namespace) -> None:
    """Capture information for the specified module (ie. run, parse and store)."""
    # Lookup the module's configuration instance based on the module specified
    module_configuration = args.modules[module]
    log.debug(f"{module_configuration=}")

    for sub_module in module_configuration.sub_modules:
        if args.sub_module and args.sub_module.lower() != sub_module.lower():
            continue
        _ingest_sub_module(args, request, module_configuration, module, sub_module.lower(), scan_request)


def _ingest_sub_module(
    args: Namespace,
    request: Request,
    module_configuration: dict,
    module: str,
    sub_module: str,
    scan_request: Namespace,
) -> None:
    scan = Scan.create(
        request=request,
        module=module,
        sub_module=sub_module,
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
        # Direct mode - run the module's command ourselves
        command = module_configuration.get_ingest_command(args.project, sub_module)
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
    parse_method = module_configuration.get_parse_method(sub_module)
    results = parse_method(json_)

    ################################################################################################
    # Save em'!
    ################################################################################################
    num = save_scan_results(scan, results)

    s_from = module.upper()
    if module.upper() != sub_module.upper():
        s_from += f"-{sub_module.upper()}"
    print(f"[green]✓ Ingested [bold]{num}[/bold] results from {s_from}[/green] as of {scan.as_of_display()}")


################################################################################################################
# ORIGINAL DON'T TOUCH!!
################################################################################################################
# def ingest_original(args: Namespace) -> None:
#     # Lookup (or create) our project!
#     project = Project.create_from_args(args)

#     # Store info obo the request
#     request = Request.create_from_args(args, project)
#     if args.git:
#         # Doing a "history" run, ie. overall git revisions over time.
#         parse_git(args, project, request)
#     else:
#         # Doing a "current" run, ie. as of this moment.
#         for module in args.modules.keys():
#             if args.module and args.module.lower() != module.lower():
#                 continue
#             parse_module(args, module, request)


# def parse_module(args: Namespace, module: str, request: Request) -> None:
#     """Capture information for the specified module (ie. run, parse and store)."""
#     # Lookup the module's configuration instance based on the module specified
#     configuration = args.modules[module]
#     log.debug(f"{configuration}")

#     for sub_module in configuration.sub_modules:
#         if args.sub_module and args.sub_module.lower() != sub_module.lower():
#             continue
#         parse_sub_module(args, request, configuration, module, sub_module)


# def parse_sub_module(args: Namespace, request: Request, configuration, module: str, sub_module: str) -> None:
#     scan = Scan.create(
#         request=request,
#         module=module.lower(),
#         sub_module=sub_module,
#         git_commit_hash=get_git_commit_hash(),
#     )

#     ################################################################################################
#     # Get the tool's data EITHER directly from stdin OR by running it!
#     ################################################################################################
#     if args.stdin:
#         # Pipeline mode - parse JSON from stdin:
#         json_ = json.loads(sys.stdin.read())
#     else:
#         # Direct mode - run the module's command ourselves
#         command = configuration.get_ingest_command(args.project, sub_module)
#         log.debug(f"{' '.join(command)=}")

#         result = subprocess.run(command, capture_output=True, check=True)
#         json_ = json.loads(result.stdout)

#     ################################################################################################
#     # Parse the results received...
#     ################################################################################################
#     parse_method = configuration.get_parse_method(sub_module)
#     results = parse_method(json_)

#     ################################################################################################
#     # Save em'!
#     ################################################################################################
#     num = save_scan_results(scan, results)

#     s_from = module.upper()
#     if module.upper() != sub_module.upper():
#         s_from += f"-{sub_module.upper()}"
#     print(f"[green]✓ Ingested [bold]{num}[/bold] results from {s_from}[/green]")


# def parse_git(args: Namespace, project: Project, request: Request) -> None:
#     repo_name = extract_repo_name(args.git)
#     log.debug(f"Project name: {project.name=} {repo_name=}")

#     for repo_path, commit_date, commit_hash in git_commits(args):
#         super_args = Namespace(
#             args=args,
#             project=project,
#             request=request,
#             repo_path=repo_path,
#             commit_date=commit_date,
#             commit_hash=commit_hash,
#         )
#         parse_git_revision(super_args)


# def parse_git_revision(super_args: Namespace) -> None:
#     args = super_args.args
#     for module in args.modules.keys():
#         if args.module and args.module.lower() != module.lower():
#             continue
#         parse_git_module(super_args, module)


# def parse_git_module(super_args: Namespace, module: str) -> None:
#     """Parse the specified module from the current revision."""
#     args = super_args.args
#     configuration = args.modules[module]
#     log.debug(f"{configuration}")

#     for sub_module in configuration.sub_modules:
#         if args.sub_module and args.sub_module.lower() != sub_module.lower():
#             continue
#         parse_git_sub_module(super_args, configuration, module, sub_module)


# def parse_git_sub_module(super_args: Namespace, configuration, module: str, sub_module: str) -> None:
#     """Parse the specified sub_module from the current revision."""
#     scan = Scan.create(
#         request=super_args.request,
#         module=module.lower(),
#         sub_module=sub_module,
#         git_commit_hash=super_args.commit_hash,
#         as_of=super_args.commit_date,  # NOTE! We're getting this from the current git revision!
#     )

#     # We're finally ready to run our module/sub_module tool against this revision
#     command = configuration.get_ingest_command(".", None)
#     log.debug(f"{' '.join(command)=}")

#     result = subprocess.run(
#         command,
#         cwd=super_args.repo_path,
#         capture_output=True,
#         check=True,
#     )
#     json_ = json.loads(result.stdout)
#     parse_method = configuration.get_parse_method(sub_module)
#     results = parse_method(json_)
#     num = save_scan_results(scan, results)

#     s_from = module.upper()
#     if module.upper() != sub_module.upper():
#         s_from += f"-{sub_module.upper()}"

#     print(f"[green]✓ Ingested [bold]{num}[/bold] results from {s_from}[/green] as of {scan.as_of_display()}")
