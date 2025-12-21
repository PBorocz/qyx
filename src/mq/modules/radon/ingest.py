"""..."""

from pathlib import Path
import json
import subprocess
import sys

from argparse import Namespace
from rich import print

from mq.modules.base import Project, Run
from mq.modules.radon import MODULE
from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from mq.utils.git import get_git_commit_hash


def ingest(args: Namespace) -> None:
    gch: str = get_git_commit_hash()
    project: Project = Project.get_or_insert(args.project)

    radon_sub_module_parse_methods = dict(
        raw=_parse_save_radon_raw_json,
        mi=_parse_save_radon_mi_json,
        hal=_parse_save_radon_hal_json,
        cc=_parse_save_radon_cc_json,
    )

    if args.stdin:
        assert args.sub_module, "Sorry, we need to have a Radon tool specified"
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())
        parser = radon_sub_module_parse_methods[args.sub_module.lower()]
        run: Run = Run.create(
            project=project.id,
            module=MODULE,
            sub_module=args.sub_module.lower(),
            git_commit_hash=gch,
        )
        num_files = parser(run, data)
        print(
            f"[green]✓ Ingested results of [bold]{num_files}[/bold] files "
            f"from radon check: {args.sub_module.upper()}[/green]",
        )

    else:
        # Direct mode - run radon ourselves across ALL the modules..
        for sub_module, parse_method in radon_sub_module_parse_methods.items():
            run: Run = Run.create(
                project=project.id,
                module=MODULE,
                sub_module=sub_module,
                git_commit_hash=gch,
            )

            sub_out = subprocess.run(["uvx", "radon", sub_module, args.project, "--json"], capture_output=True)

            data = json.loads(sub_out.stdout)

            num_files = parse_method(run, data)
            print(
                f"[green]✓ Ingested results of [bold]{num_files}[/bold] files from radon check: {sub_module.upper()}[/green]"
            )


def _parse_save_radon_raw_json(run: Run, data: dict[str, int]) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        return RadonRaw(
            dir=fn_path.parent,
            filename=fn_path.name,
            loc=radon_result["loc"],
            lloc=radon_result["lloc"],
            sloc=radon_result["sloc"],
            comments=radon_result["comments"],
            multi=radon_result["multi"],
            blank=radon_result["blank"],
            single_comments=radon_result["single_comments"],
        )

    rows = [_json_to_row(fn_, results) for fn_, results in data.items()]
    return _save_results(run, rows)


def _parse_save_radon_mi_json(run: Run, data: dict[str, int]) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        return RadonMi(
            dir=fn_path.parent,
            filename=fn_path.name,
            mi=radon_result["mi"],
            rank=radon_result["rank"],
        )

    rows = [_json_to_row(fn_, results) for fn_, results in data.items()]
    return _save_results(run, rows)


def _parse_save_radon_cc_json(run: Run, data: dict[str, int]) -> int:
    num_files = 0
    for fn_, entities in data.items():
        fn_path = Path(fn_)
        for entity in entities:
            row = RadonCc(
                run=run.id,
                dir=fn_path.parent,
                filename=fn_path.name,
                entity_type=entity["type"][0].upper(),
                entity_name=entity["name"],
                line_start=entity["lineno"],
                line_end=entity["endline"],
                column_offset=entity["col_offset"],
                complexity=entity["complexity"],
                rank=entity["rank"],
            )
            row.save()
        num_files += 1
    return num_files


def _parse_save_radon_hal_json(run: Run, data: dict[str, int]) -> int:
    # Have to do this nested to reflect json file structure:
    num_files = 0
    for fn_, results in data.items():
        total = results["total"]
        fn_path = Path(fn_)
        radon_hal = RadonHal(
            run=run.id,
            dir=fn_path.parent,
            filename=fn_path.name,
            h1=total["h1"],
            h2=total["h2"],
            N1=total["N1"],
            N2=total["N2"],
            program_vocabulary=total["vocabulary"],
            program_length=total["length"],
            calculated_length=total["calculated_length"],
            volume=total["volume"],
            difficulty=total["difficulty"],
            effort=total["effort"],
            time=total["time"],
            bugs=total["bugs"],
        )
        radon_hal.save()
        num_files += 1

        for func_name, func_results in results.get("functions", {}).items():
            radon_hal_func = RadonHalFunction(
                run=run.id,
                radon_hal_id=radon_hal.id,
                name=func_name,
                h1=func_results["h1"],
                h2=func_results["h2"],
                N1=func_results["N1"],
                N2=func_results["N2"],
                program_vocabulary=func_results["vocabulary"],
                program_length=func_results["length"],
                calculated_length=func_results["calculated_length"],
                volume=func_results["volume"],
                difficulty=func_results["difficulty"],
                effort=func_results["effort"],
                time=func_results["time"],
                bugs=func_results["bugs"],
            )
            radon_hal_func.save()

    return num_files


def _save_results(run: Run, rows: list[RadonRaw]) -> int:
    for row in rows:
        row.run = run.id
        row.save()
    return len(rows)
