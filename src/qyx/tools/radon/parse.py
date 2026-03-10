"""..."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from qyx.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from qyx.tools._models_ import Scan

log = logging.getLogger(__name__)


def parse_raw(scan: Scan, data: Any) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw | None:
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
        try:
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
        except KeyError:
            log.error(f"Unable to parse radon raw: {fn_}[{scan.git_commit_hash[:8]}] {radon_result=}")
            return None

    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon raw scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    rows = [_json_to_row(fn_, results) for fn_, results in json_.items()]
    for row in rows:
        if row:
            row.scan = scan.id
            row.save()
    return len(rows)


def parse_mi(scan: Scan, data: Any) -> int:
    def _json_to_row(fn_: str, radon_result: dict[str, int]) -> RadonRaw | None:
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
        try:
            return RadonMi(
                directory=fn_path.parent,
                filename=fn_path.name,
                mi=radon_result["mi"],
                rank=radon_result["rank"],
            )
        except KeyError:
            log.error(f"Unable to parse radon mi: {fn_}[{scan.git_commit_hash[:8]}] {radon_result=}")
            return None

    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon mi scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    rows = [_json_to_row(fn_, results) for fn_, results in json_.items()]
    for row in rows:
        if row:  # Skip the entries that had errors..
            row.scan = scan.id
            row.save()
    return len(rows)


def parse_cc(scan: Scan, data: Any) -> int:
    rows = []
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon cc scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    for fn_, entities in json_.items():
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
        for entity in entities:
            entity_type = entity["type"][0].upper()
            if not RadonCc.entity_type_display(entity_type):
                log.error(
                    f"Invalid/unexpected EntityType encountered: '{entity_type}', expecting one of 'C', 'M', or 'F'",
                )
                continue

            row = RadonCc(
                directory=fn_path.parent,
                filename=fn_path.name,
                entity_type=entity_type,
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


def parse_hal(scan: Scan, data: Any) -> int:
    # Have to do this nested to reflect json file structure:
    count = 0
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon hal scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    for fn_, results in json_.items():
        try:
            total = results["total"]
        except KeyError:
            # Radon encountered an error parsing the file..
            log.error(f"Unable to parse radon hal: {fn_}[{scan.git_commit_hash[:8]}] {results=}")
            continue

        # (if we get this far, most likely the entry is good and we don't need to check for KeyError.)
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
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
