#!/usr/bin/env python
"""Build a sample_id-to-BAM manifest from metadata and a path pattern."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = ("sample_id", "bam_path")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-column", default="sample_alias")
    parser.add_argument("--omics-column", default="omics")
    parser.add_argument("--omics-value", default="MG")
    parser.add_argument(
        "--bam-pattern",
        required=True,
        help="Pattern with {sample_id}, for example /path/{sample_id}/{sample_id}.rmag.bam",
    )
    parser.add_argument("--require-existing", action="store_true")
    args = parser.parse_args()

    rows = read_tsv(args.metadata)
    output_rows = []
    seen = set()
    for row in rows:
        if args.omics_column in row and args.omics_value and row[args.omics_column] != args.omics_value:
            continue
        sample_id = row.get(args.sample_column, "")
        if not sample_id or sample_id in seen:
            continue
        seen.add(sample_id)
        bam_path = args.bam_pattern.format(sample_id=sample_id)
        if args.require_existing and not Path(bam_path).exists():
            continue
        output_rows.append({"sample_id": sample_id, "bam_path": bam_path})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == "__main__":
    main()
