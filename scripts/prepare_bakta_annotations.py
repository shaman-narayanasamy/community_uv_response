#!/usr/bin/env python
"""Normalize Bakta TSV outputs into the UV annotation table schema."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = ("MAG_ID", "gene_id", "gene_symbol", "gene_function")
GENE_COLUMNS = ("Gene", "gene", "gene_symbol")
PRODUCT_COLUMNS = ("Product", "product", "gene_function")
ID_COLUMNS = ("Locus Tag", "locus_tag", "ID", "gene_id")


def pick(row: dict[str, str], columns: tuple[str, ...]) -> str:
    for column in columns:
        if column in row and row[column]:
            return row[column]
    return ""


def mag_id_from_path(path: Path) -> str:
    if path.parent.name and path.parent.name != "bakta":
        return path.parent.name
    return path.stem


def bakta_tables(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.tsv") if not path.name.startswith("."))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bakta-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = []
    for path in bakta_tables(args.bakta_root):
        mag_id = mag_id_from_path(path)
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None:
                continue
            for row in reader:
                feature_type = row.get("Type") or row.get("type") or ""
                if feature_type and feature_type != "CDS":
                    continue
                gene_id = pick(row, ID_COLUMNS)
                gene_function = pick(row, PRODUCT_COLUMNS)
                if not gene_id and not gene_function:
                    continue
                rows.append(
                    {
                        "MAG_ID": mag_id,
                        "gene_id": gene_id,
                        "gene_symbol": pick(row, GENE_COLUMNS),
                        "gene_function": gene_function,
                    }
                )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
