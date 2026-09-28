#!/usr/bin/env python
"""Create a gene coverage manifest from quantification TSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


COLUMNS = ("sample_id", "run_id", "data_type", "path")


def infer_sample_id(path: Path) -> str:
    stem = path.stem
    if "__" in stem:
        return stem.split("__", 1)[0]
    return stem.split("_", 1)[0]


def infer_data_type(path: Path) -> str:
    parent = path.parent.name
    if parent in {"metagenomics", "metatranscriptomics"}:
        return parent
    stem = path.stem
    if stem.endswith("_metagenomics"):
        return "metagenomics"
    if stem.endswith("_metatranscriptomics"):
        return "metatranscriptomics"
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--relative-paths", action="store_true")
    args = parser.parse_args()

    rows = []
    for path in sorted(args.coverage_root.rglob("*.tsv")):
        out_path = path if args.relative_paths else path.resolve()
        rows.append(
            {
                "sample_id": infer_sample_id(path),
                "run_id": path.stem,
                "data_type": infer_data_type(path),
                "path": str(out_path),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
