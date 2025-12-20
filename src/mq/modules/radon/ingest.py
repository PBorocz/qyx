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

    if args.stdin:
        # Pipeline mode - parse JSON from stdin
        data = json.loads(sys.stdin.read())

        # FIXME: Can we make the determination of which module dynamic based on json contents??
        # sub_module = BUILD_ME!
        # Parse me!
        raise RuntimeError("Sorry, we can't identify the sub_module from the json...YET!")

    else:
        radon_sub_modules = dict(
            raw=_parse_save_radon_raw_json,
            mi=_parse_save_radon_mi_json,
            hal=_parse_save_radon_hal_json,
            cc=_parse_save_radon_cc_json,
        )
        # Direct mode - run radon ourselves across ALL the modules..
        for sub_module, parse_method in radon_sub_modules.items():
            run: Run = Run(
                project=project.id,
                module=MODULE,
                sub_module=sub_module,
                git_commit_hash=gch,
            )
            run.save()

            sub_out = subprocess.run(["uvx", "radon", sub_module, args.project, "--json"], capture_output=True)

            data = json.loads(sub_out.stdout)

            num_files = parse_method(run, data)
            print(
                f"[green]✓ Ingested results of [bold]{num_files}[/bold] files from radon check: {sub_module.upper()}[/green]"
            )

    # num_functions = None
    # if args.sub_module == "raw":
    #     num_files = _parse_save_radon_raw_json(run, data)
    #     msg = f"Ingested {num_files} results from radon check: RAW"
    # elif args.sub_module == "mi":
    #     num_files = _parse_save_radon_mi_json(run, data)
    #     msg = f"Ingested {num_files} results from radon check: MI"
    # elif args.sub_module == "hal":
    #     num_files, num_functions = _parse_save_radon_hal_json(run, data)
    #     msg = f"Ingested {num_files} files and with {num_functions} functions from radon check: HAL"
    # elif args.sub_module == "cc":
    #     num_files, num_entities = _parse_save_radon_cc_json(run, data)
    #     msg = f"Ingested {num_files} files and with {num_entities} entities from radon check: CC"
    # else:
    #     logger.error(f"Sorry, we don't support sub_module: {args.sub_module} yet!")

    # logger.info(msg)


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
            radon_hal_func.save()

    return num_files


def _save_results(run: Run, rows: list[RadonRaw]) -> int:
    for row in rows:
        row.run = run.id
        row.save()
    return len(rows)
