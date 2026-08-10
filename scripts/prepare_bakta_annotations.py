#!/usr/bin/env python
"""Normalize primary Bakta TSV outputs into the UV annotation table schema."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TextIO


OUTPUT_COLUMNS = ("MAG_ID", "gene_id", "gene_symbol", "gene_function")
DUPLICATE_COLUMNS = (
    "MAG_ID",
    "gene_id",
    "duplicate_status",
    "first_source",
    "duplicate_source",
    "first_gene_symbol",
    "first_gene_function",
    "duplicate_gene_symbol",
    "duplicate_gene_function",
)
GENE_COLUMNS = ("Gene", "gene", "gene_symbol")
PRODUCT_COLUMNS = ("Product", "product", "gene_function")
ID_COLUMNS = ("Locus Tag", "locus_tag", "ID", "gene_id")
TYPE_COLUMNS = ("Type", "type")
COMPANION_SUFFIXES = (".inference.tsv", ".hypotheticals.tsv")


def pick(row: dict[str, str], columns: tuple[str, ...]) -> str:
    for column in columns:
        value = row.get(column, "").strip()
        if value:
            return value
    return ""


def is_companion_table(path: Path) -> bool:
    name = path.name.casefold()
    return any(name.endswith(suffix) for suffix in COMPANION_SUFFIXES)


def bakta_tables(root: Path) -> list[Path]:
    """Select primary Bakta TSVs and reject ambiguous nested layouts.

    The canonical layout is ``<root>/<MAG_ID>/<MAG_ID>.tsv``. A directory with
    one non-companion TSV is accepted as an equivalent layout. A flat root of
    primary TSV files is also accepted. Known Bakta companion tables are never
    selected.
    """

    if not root.exists():
        raise FileNotFoundError(f"Bakta input does not exist: {root}")
    if root.is_file():
        if is_companion_table(root):
            raise ValueError(f"Bakta companion table is not a primary annotation table: {root}")
        return [root]

    candidates = sorted(
        path
        for path in root.rglob("*.tsv")
        if not path.name.startswith(".") and not is_companion_table(path)
    )
    by_directory: dict[Path, list[Path]] = defaultdict(list)
    for path in candidates:
        by_directory[path.parent].append(path)

    selected: list[Path] = []
    for directory, paths in sorted(by_directory.items()):
        canonical = [path for path in paths if path.stem == directory.name]
        if len(canonical) == 1:
            selected.append(canonical[0])
        elif directory == root:
            selected.extend(paths)
        elif len(paths) == 1:
            selected.append(paths[0])
        else:
            choices = ", ".join(str(path) for path in paths)
            raise ValueError(f"Ambiguous primary Bakta TSVs under {directory}: {choices}")

    if not selected:
        raise ValueError(f"No primary Bakta TSV tables found under {root}")
    return sorted(selected)


def mag_id_from_path(path: Path, root: Path) -> str:
    if root.is_file() or path.parent == root:
        return path.stem
    return path.parent.name


def source_label(path: Path, root: Path) -> str:
    if root.is_file():
        return path.name
    return str(path.relative_to(root))


def bakta_tsv_lines(handle: TextIO, path: Path) -> Iterator[str]:
    """Yield a standard header plus data rows from a Bakta TSV stream."""

    header_found = False
    for line in handle:
        if not line.strip():
            continue
        if not header_found:
            candidate = line[1:] if line.startswith("#") else line
            fields = candidate.rstrip("\r\n").split("\t")
            has_id = any(column in fields for column in ID_COLUMNS)
            has_type = any(column in fields for column in TYPE_COLUMNS)
            if has_id and has_type:
                header_found = True
                yield candidate
            elif not line.startswith("#"):
                raise ValueError(f"Could not identify a Bakta TSV header in {path}")
            continue

        if line.startswith("#"):
            continue
        yield line

    if not header_found:
        raise ValueError(f"Could not identify a Bakta TSV header in {path}")


def count_companion_tables(root: Path) -> int:
    if root.is_file():
        return int(is_companion_table(root))
    return sum(1 for path in root.rglob("*.tsv") if is_companion_table(path))


def write_tsv(path: Path, columns: tuple[str, ...], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bakta-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--duplicates-output",
        type=Path,
        help="Optional audit TSV for exact and conflicting duplicate MAG/gene IDs.",
    )
    parser.add_argument(
        "--fail-on-conflicts",
        action="store_true",
        help="Do not write the annotation table when conflicting duplicates are detected.",
    )
    args = parser.parse_args()

    tables = bakta_tables(args.bakta_root)
    companion_count = count_companion_tables(args.bakta_root)
    print(
        f"Selected {len(tables)} primary Bakta TSV table(s); "
        f"excluded {companion_count} companion table(s).",
        file=sys.stderr,
    )

    rows: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    seen: dict[tuple[str, str], tuple[dict[str, str], str]] = {}
    conflict_count = 0

    for path in tables:
        mag_id = mag_id_from_path(path, args.bakta_root)
        source = source_label(path, args.bakta_root)
        with path.open(newline="") as handle:
            reader = csv.DictReader(bakta_tsv_lines(handle, path), delimiter="\t")
            for raw_row in reader:
                feature_type = pick(raw_row, TYPE_COLUMNS)
                if feature_type and feature_type.casefold() != "cds":
                    continue
                row = {
                    "MAG_ID": mag_id,
                    "gene_id": pick(raw_row, ID_COLUMNS),
                    "gene_symbol": pick(raw_row, GENE_COLUMNS),
                    "gene_function": pick(raw_row, PRODUCT_COLUMNS),
                }
                if not row["gene_id"] and not row["gene_function"]:
                    continue

                key = (row["MAG_ID"], row["gene_id"])
                if row["gene_id"] and key in seen:
                    first_row, first_source = seen[key]
                    is_exact = all(first_row[column] == row[column] for column in OUTPUT_COLUMNS)
                    duplicate_status = "exact_duplicate" if is_exact else "conflicting_duplicate"
                    conflict_count += int(not is_exact)
                    duplicates.append(
                        {
                            "MAG_ID": row["MAG_ID"],
                            "gene_id": row["gene_id"],
                            "duplicate_status": duplicate_status,
                            "first_source": first_source,
                            "duplicate_source": source,
                            "first_gene_symbol": first_row["gene_symbol"],
                            "first_gene_function": first_row["gene_function"],
                            "duplicate_gene_symbol": row["gene_symbol"],
                            "duplicate_gene_function": row["gene_function"],
                        }
                    )
                    continue

                if row["gene_id"]:
                    seen[key] = (row, source)
                rows.append(row)

    if args.duplicates_output:
        write_tsv(args.duplicates_output, DUPLICATE_COLUMNS, duplicates)

    print(
        f"Prepared {len(rows)} annotation row(s); detected {len(duplicates)} duplicate row(s), "
        f"including {conflict_count} conflict(s).",
        file=sys.stderr,
    )
    if conflict_count and args.fail_on_conflicts:
        raise SystemExit(
            f"Detected {conflict_count} conflicting duplicate MAG/gene ID(s); "
            "annotation output was not written."
        )

    write_tsv(args.output, OUTPUT_COLUMNS, rows)


if __name__ == "__main__":
    main()
