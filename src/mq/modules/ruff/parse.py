"""..."""

# import json
# import subprocess
# import sys
# from argparse import Namespace
from pathlib import Path

# from rich import print

# from mq.modules.base import Project, Request, Scan
# from mq.modules import save_scan_results
# from mq.modules.ruff import MODULE
from mq.modules.ruff.models import Ruff
# from mq.utils.git import get_git_commit_hash


# def ingest(args: Namespace) -> None:
#     current_git_commit_hash = get_git_commit_hash()
#     project = Project.get_or_insert_relative(args.project)
#     request = Request.create(project=project, module=MODULE)
#     scan = Scan.create(request=request, module=MODULE, git_commit_hash=current_git_commit_hash)

#     if args.stdin:
#         # Pipeline mode - parse JSON from stdin
#         json_data = json.loads(sys.stdin.read())
#     else:
#         # Direct mode - run ruff ourselves
#         result = subprocess.run(
#             ["ruff", "check", "--output-format=json", args.project],
#             capture_output=True,
#         )
#         json_data = json.loads(result.stdout)

#     results = _parse_ruff_json(json_data)
#     if results:
#         num = save_scan_results(scan, results)
#         print(f"[green]✓ Ingested [bold]{num}[/bold] results from ruff check[/green]")
#     else:
#         print("[green]✓ [bold]Congrulation![/bold] All checks passed![/green]")


def parse_json(data: list) -> list[Ruff]:
    def _json_to_row(ruff_result: dict) -> Ruff:
        fn_path = Path(ruff_result["filename"])
        return Ruff(
            dir=fn_path.parent,
            filename=fn_path.name,
            line=ruff_result["location"]["row"],
            column=ruff_result["location"]["column"],
            message=ruff_result["message"],
            rule_code=ruff_result["code"],
            url=ruff_result["url"],
        )

    return [_json_to_row(check) for check in data]
