# """..."""

# from pathlib import Path
# import json
# import subprocess
# import sys

# from argparse import Namespace
# from rich import print

# from mq.modules.base import Project, Request, Scan
# from mq.modules.radon import MODULE
# from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
# from mq.utils.git import get_git_commit_hash


# def ingest(args: Namespace) -> None:
#     gch: str = get_git_commit_hash()
#     project: Project = Project.get_or_insert_relative(args.project)

#     radon_sub_module_parse_methods = dict(
#         raw=_parse_save_radon_raw_json,
#         mi=_parse_save_radon_mi_json,
#         hal=_parse_save_radon_hal_json,
#         cc=_parse_save_radon_cc_json,
#     )

#     if args.stdin:
#         assert args.sub_module, "Sorry, we need to have a Radon tool specified"
#         # Pipeline mode - parse JSON from stdin
#         data = json.loads(sys.stdin.read())
#         parser = radon_sub_module_parse_methods[args.sub_module.lower()]
#         run: Run = Run.create(
#             project=project.id,
#             module=MODULE,
#             sub_module=args.sub_module.lower(),
#             git_commit_hash=gch,
#         )
#         num_files = parser(run, data)
#         print(
#             f"[green]✓ Ingested results of [bold]{num_files}[/bold] files "
#             f"from radon check: {args.sub_module.upper()}[/green]",
#         )

#     else:
#         # Direct mode - run radon ourselves across ALL the modules..
#         for sub_module, parse_method in radon_sub_module_parse_methods.items():
#             run: Run = Run.create(
#                 project=project.id,
#                 module=MODULE,
#                 sub_module=sub_module,
#                 git_commit_hash=gch,
#             )

#             sub_out = subprocess.run(["uvx", "radon", sub_module, args.project, "--json"], capture_output=True)

#             data = json.loads(sub_out.stdout)

#             num_files = parse_method(run, data)
#             print(
#                 f"[green]✓ Ingested results of [bold]{num_files}[/bold] "
#                 f"files from radon check: {sub_module.upper()}[/green]",
#             )
