"""..."""

import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from qyx.tools.radon.models import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from qyx.tools._models_ import Scan

log = logging.getLogger(__name__)


def parse_raw(scan: Scan, latest: bool, data: Any) -> int:
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

    def _get_summary(rows: list[RadonRaw]) -> dict:
        return_ = defaultdict(int)
        for row in rows:
            for attr in ("loc", "lloc", "sloc", "comments", "multi", "blank", "single_comments"):
                return_[attr] += getattr(row, attr, 0)
        return return_

    # GO!
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon raw scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    rows = [_json_to_row(fn_, results) for fn_, results in json_.items()]

    # Save summary information (always)
    scan.summary = _get_summary(rows)
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            if row:
                row.scan = scan.id
                row.save()
    return len(rows)


def parse_mi(scan: Scan, latest: bool, data: Any) -> int:
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

    def _get_summary(rows: list[RadonMi]) -> dict:
        """Calculate LOC-weighted Maintainability Index (using latest loc/raw RAW scan)."""
        # Get the number of lines of code at the moment from the latest "raw" scan..
        raw_scan = Scan.get_latest(scan.request.project, "radon", "raw")
        loc_per_dir_filename = defaultdict(int)
        for raw in RadonRaw.select().where(RadonRaw.scan_id == raw_scan.id):
            key = (raw.directory, raw.filename)
            loc_per_dir_filename[key] += raw.loc
        total_loc = sum(loc_per_dir_filename.values())

        # Calculate the MI weighted by the lines of code in each respective file.
        total_weighted_sum = 0.0
        for row in rows:
            try:
                key = (str(row.directory), row.filename)
                loc = loc_per_dir_filename.get(key, 0)
                total_weighted_sum += loc * row.mi
            except AttributeError:
                breakpoint()

                ...

        weighted_avg_mi = total_weighted_sum / total_loc if total_loc else 0.0

        return {"maintainability_index": weighted_avg_mi}

    # GO!
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon mi scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    rows = [_json_to_row(fn_, results) for fn_, results in json_.items()]

    # Save summary information (always)
    scan.summary = _get_summary(rows)
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            if row:  # Skip the entries that had errors..
                row.scan = scan.id
                row.save()
    return len(rows)


def parse_cc(scan: Scan, latest: bool, data: Any) -> int:
    def _get_summary(rows: list[RadonCc]) -> dict:
        totals = defaultdict(float)
        counts = defaultdict(int)
        for row in rows:
            totals[row.entity_type] += row.complexity
            counts[row.entity_type] += 1

        avg_complexity = {entity_type: total / counts[entity_type] for entity_type, total in totals.items()}

        return {"mean_complexity": dict(avg_complexity)}

    rows = []
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon cc scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    for fn_, entities in json_.items():
        fn_path = Path(os.path.relpath(Path(fn_), scan.cwd))
        for entity in entities:
            try:
                entity_type = entity["type"][0].upper()
            except TypeError as exc:
                log.error(f"Unable to parse radon cc scan: [{scan.git_commit_hash[:8]}] {exc=} {entity=}")
                continue

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

    # Save summary information (always)
    scan.summary = _get_summary(rows)
    scan.save()

    # Save detail information if this is putatively the most recent scan!
    if latest:
        for row in rows:
            row.scan = scan.id
            row.save()

    return len(rows)


def parse_hal(scan: Scan, latest: bool, data: Any) -> int:
    # Have to do this nested to reflect json file structure:
    count = 0
    try:
        json_ = json.loads(data)
    except json.decoder.JSONDecodeError as exc:
        log.error(f"Unable to parse radon hal scan results (bad JSON)!: [{scan.git_commit_hash[:8]}] {exc=} {data=}")
        return 0

    rows = []
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
        # Save detail information if this is putatively the most recent scan!
        if latest:
            radon_hal.save()
        count += 1
        rows.append(radon_hal)

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
            if latest:
                radon_hal_func.save()

    # Save summary information (always)
    scan.summary = _get_summary_hal(rows)
    scan.save()

    return count


def _get_summary_hal(rows: list[RadonHal]) -> dict:
    totals = defaultdict(float)
    for row in rows:
        for attr in [o_attr.name for o_attr in RadonHal.attrs()]:
            totals[attr] += getattr(row, attr, 0)
    return_avgs = defaultdict(float)
    for attr in [o_attr.name for o_attr in RadonHal.attrs()]:
        return_avgs[attr] /= len(rows)

    return return_avgs
