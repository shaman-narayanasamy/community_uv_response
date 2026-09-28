#!/usr/bin/env python
"""Normalize CenoteTaker3 gene annotations into the UV annotation schema."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = ("entity_type", "entity_id", "MAG_ID", "gene_id", "gene_symbol", "gene_function")


def read_contig_map(path: Path) -> dict[str, str]:
    mapping = {}
    with path.open(newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if len(row) >= 2:
                mapping[row[0]] = row[1]
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cenote-summary", required=True, type=Path)
    parser.add_argument("--contig-map", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    contig_map = read_contig_map(args.contig_map)
    rows = []
    with args.cenote_summary.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{args.cenote_summary} is empty or missing a header")
        required = {"contig", "gene_name", "evidence_description"}
        missing = required.difference(reader.fieldnames)
        if missing:
            raise SystemExit(f"{args.cenote_summary} missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            gene_id = row.get("gene_name", "")
            entity_id = contig_map.get(row.get("contig", ""), row.get("contig", ""))
            function = row.get("evidence_description", "")
            if not gene_id or not entity_id:
                continue
            rows.append(
                {
                    "entity_type": "vOTU",
                    "entity_id": entity_id,
                    "MAG_ID": entity_id,
                    "gene_id": gene_id,
                    "gene_symbol": "",
                    "gene_function": function,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
