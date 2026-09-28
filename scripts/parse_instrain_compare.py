#!/usr/bin/env python
"""Normalize inStrain comparison summaries and rMAG-level divergence metrics."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


COMPARE_COLUMNS = (
    "genome",
    "sample_a",
    "sample_b",
    "condition_a",
    "condition_b",
    "cycle_a",
    "cycle_b",
    "coverage_status",
    "popANI",
    "compared_bases_count",
    "SNV_distance",
)
RMAG_COLUMNS = (
    "MAG_ID",
    "comparison_axis",
    "comparison_label",
    "n_valid_pairs",
    "mean_snv_distance",
    "mean_popani",
    "interpretation_status",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def sample_id(row: dict[str, str]) -> str:
    return row.get("sample_id") or row.get("sample_alias") or ""


def as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-table", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--compare-summary-output", required=True, type=Path)
    parser.add_argument("--rmag-output", required=True, type=Path)
    args = parser.parse_args()

    compare_rows = read_tsv(args.compare_table)
    metadata = read_tsv(args.metadata)
    metadata_by_sample = {sample_id(row): row for row in metadata}

    required = {"sample_a", "sample_b", "popANI", "compared_bases_count", "SNV_distance"}
    if compare_rows:
        present = set(compare_rows[0])
        if "genome" not in present and "MAG_ID" not in present:
            raise SystemExit(f"{args.compare_table} missing required column: genome or MAG_ID")
        missing = sorted(required - present)
        if missing:
            raise SystemExit(f"{args.compare_table} missing required columns: {', '.join(missing)}")

    normalized = []
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in compare_rows:
        genome = row.get("genome") or row.get("MAG_ID", "")
        meta_a = metadata_by_sample.get(row["sample_a"], {})
        meta_b = metadata_by_sample.get(row["sample_b"], {})
        compared_bases = as_float(row["compared_bases_count"])
        coverage_status = "valid" if compared_bases and compared_bases > 0 else "low_coverage"
        output_row = {
            "genome": genome,
            "sample_a": row["sample_a"],
            "sample_b": row["sample_b"],
            "condition_a": meta_a.get("condition", ""),
            "condition_b": meta_b.get("condition", ""),
            "cycle_a": meta_a.get("cycle", ""),
            "cycle_b": meta_b.get("cycle", ""),
            "coverage_status": coverage_status,
            "popANI": row["popANI"],
            "compared_bases_count": row["compared_bases_count"],
            "SNV_distance": row["SNV_distance"],
        }
        normalized.append(output_row)
        if coverage_status == "valid":
            label = f"{output_row['condition_a']}__vs__{output_row['condition_b']}"
            groups[(genome, "condition", label)].append(output_row)

    rmag_rows = []
    for (genome, axis, label), rows in sorted(groups.items()):
        snv_values = [as_float(row["SNV_distance"]) for row in rows]
        popani_values = [as_float(row["popANI"]) for row in rows]
        snv_values = [value for value in snv_values if value is not None]
        popani_values = [value for value in popani_values if value is not None]
        rmag_rows.append(
            {
                "MAG_ID": genome,
                "comparison_axis": axis,
                "comparison_label": label,
                "n_valid_pairs": len(rows),
                "mean_snv_distance": f"{sum(snv_values) / len(snv_values):.6g}" if snv_values else "",
                "mean_popani": f"{sum(popani_values) / len(popani_values):.6g}" if popani_values else "",
                "interpretation_status": "strain_divergence_summary",
            }
        )

    for path, rows, columns in (
        (args.compare_summary_output, normalized, COMPARE_COLUMNS),
        (args.rmag_output, rmag_rows, RMAG_COLUMNS),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, columns, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
