"""..."""

from pathlib import Path
import json
import subprocess
import sys

from argparse import Namespace
from rich import print

from mq.modules.base import Project, Request, Scan
from mq.modules.radon import MODULE
from mq.modules.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from mq.utils.git import get_git_commit_hash


def parse_json_raw(data: dict[str, int]) -> int:
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

    return [_json_to_row(fn_, results) for fn_, results in data.items()]


def parse_json_mi(data: dict[str, int]) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        return RadonMi(
            dir=fn_path.parent,
            filename=fn_path.name,
            mi=radon_result["mi"],
            rank=radon_result["rank"],
        )

    return [_json_to_row(fn_, results) for fn_, results in data.items()]


def parse_json_cc(data: dict[str, int]) -> int:
    mapping = dict(F="Function", M="Method", C="Class")
    rows = []
    for fn_, entities in data.items():
        fn_path = Path(fn_)
        for entity in entities:
            row = RadonCc(
                dir=fn_path.parent,
                filename=fn_path.name,
                entity_type=mapping[entity["type"][0].upper()],
                entity_name=entity["name"],
                line_start=entity["lineno"],
                line_end=entity["endline"],
                column_offset=entity["col_offset"],
                complexity=entity["complexity"],
                rank=entity["rank"],
            )
            rows.append(row)
    return rows


def parse_json_hal(data: dict[str, int]) -> int:
    # Have to do this nested to reflect json file structure:
    rows = []
    for fn_, results in data.items():
        total = results["total"]
        fn_path = Path(fn_)
        rows.append(
            RadonHal(
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
            ),
        )

        # FOR NOW: WE DON"T EVEN USE Function data.
        # If we do, we need to figure out a way to save them "after the fact"
        # given that at this stage, we don't have actual RadonHal database instances yet!
        # for func_name, func_results in results.get("functions", {}).items():
        #     radon_hal_func = RadonHalFunction(
        #         radon_hal=radon_hal,
        #         name=func_name,
        #         h1=func_results["h1"],
        #         h2=func_results["h2"],
        #         N1=func_results["N1"],
        #         N2=func_results["N2"],
        #         program_vocabulary=func_results["vocabulary"],
        #         program_length=func_results["length"],
        #         calculated_length=func_results["calculated_length"],
        #         volume=func_results["volume"],
        #         difficulty=func_results["difficulty"],
        #         effort=func_results["effort"],
        #         time=func_results["time"],
        #         bugs=func_results["bugs"],
        #     )
        #     radon_hal_func.save()

    return rows
