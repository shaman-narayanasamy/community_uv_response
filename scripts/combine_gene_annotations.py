#!/usr/bin/env python
"""Concatenate normalized gene annotation tables with a single header."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = ("entity_type", "entity_id", "MAG_ID", "gene_id", "gene_symbol", "gene_function")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = []
    for path in args.annotations:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None:
                continue
            if "entity_id" not in reader.fieldnames and "MAG_ID" not in reader.fieldnames:
                raise SystemExit(f"{path} missing required entity column: entity_id or MAG_ID")
            for row in reader:
                entity_id = row.get("entity_id") or row.get("MAG_ID", "")
                entity_type = row.get("entity_type") or "MAG"
                rows.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "MAG_ID": row.get("MAG_ID") or entity_id,
                        "gene_id": row.get("gene_id", ""),
                        "gene_symbol": row.get("gene_symbol", ""),
                        "gene_function": row.get("gene_function", ""),
                    }
                )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
