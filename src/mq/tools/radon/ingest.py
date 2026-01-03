"""..."""

import os
from pathlib import Path

from mq.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from mq.tools.base import Scan


def ingest_raw(scan: Scan, data: dict[str, int]) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        return RadonRaw(
            directory=fn_path.parent,
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
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


def ingest_mi(scan: Scan, data: dict[str, int]) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw:
        fn_path = Path(fn_)
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        return RadonMi(
            directory=fn_path.parent,
            filename=fn_path.name,
            mi=radon_result["mi"],
            rank=radon_result["rank"],
        )

    rows = [_json_to_row(fn_, results) for fn_, results in data.items()]
    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


def ingest_cc(scan: Scan, data: dict[str, int]) -> int:
    mapping = dict(F="Function", M="Method", C="Class")
    rows = []
    for fn_, entities in data.items():
        fn_path = Path(fn_)
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        for entity in entities:
            row = RadonCc(
                directory=fn_path.parent,
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

    for row in rows:
        row.scan = scan.id
        row.save()
    return len(rows)


def ingest_hal(scan: Scan, data: dict[str, int]) -> int:
    # Have to do this nested to reflect json file structure:
    count = 0
    for fn_, results in data.items():
        total = results["total"]
        fn_path = Path(fn_)
        fn_path = Path(os.path.relpath(fn_path, scan.cwd))
        radon_hal = RadonHal(
            scan=scan.id,
            directory=fn_path.parent,
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
        count += 1

        for func_name, func_results in results.get("functions", {}).items():
            radon_hal_func = RadonHalFunction(
                scan=scan.id,
                radon_hal=radon_hal,
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

    return count
