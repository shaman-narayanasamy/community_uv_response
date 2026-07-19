#!/usr/bin/env python
"""Join long-format gene expression counts to UV signature hits."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = (
    "MAG_ID",
    "gene_id",
    "sample_id",
    "condition",
    "phase",
    "cycle",
    "analysis_group",
    "raw_count",
    "normalized_count",
    "signature_tier",
    "signature_category",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def require_columns(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    present = set(rows[0].keys()) if rows else set()
    missing = [column for column in columns if column not in present]
    if missing:
        raise SystemExit(f"{path} missing required columns: {', '.join(missing)}")


def sample_id(row: dict[str, str]) -> str:
    return row.get("sample_id") or row.get("sample_alias") or ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hits", required=True, type=Path)
    parser.add_argument("--expression", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    hits = read_tsv(args.hits)
    expression = read_tsv(args.expression)
    metadata = read_tsv(args.metadata)
    if not hits:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="") as handle:
            csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n").writeheader()
        return

    require_columns(args.hits, hits, ("MAG_ID", "gene_id", "signature_tier", "signature_category"))
    require_columns(args.expression, expression, ("gene_id",))
    if "sample_id" not in expression[0] and "sample_alias" not in expression[0]:
        raise SystemExit(f"{args.expression} missing required sample column: sample_id or sample_alias")
    if "raw_count" not in expression[0] and "count" not in expression[0]:
        raise SystemExit(f"{args.expression} missing required count column: raw_count or count")
    if metadata and "sample_id" not in metadata[0] and "sample_alias" not in metadata[0]:
        raise SystemExit(f"{args.metadata} missing required sample column: sample_id or sample_alias")

    hits_by_gene: dict[str, list[dict[str, str]]] = {}
    for hit in hits:
        hits_by_gene.setdefault(hit["gene_id"], []).append(hit)

    metadata_by_sample = {sample_id(row): row for row in metadata}
    rows = []
    for expr in expression:
        sid = sample_id(expr)
        meta = metadata_by_sample.get(sid, {})
        for hit in hits_by_gene.get(expr["gene_id"], []):
            rows.append(
                {
                    "MAG_ID": hit["MAG_ID"],
                    "gene_id": hit["gene_id"],
                    "sample_id": sid,
                    "condition": meta.get("condition", ""),
                    "phase": meta.get("phase", ""),
                    "cycle": meta.get("cycle", ""),
                    "analysis_group": meta.get("analysis_group", ""),
                    "raw_count": expr.get("raw_count") or expr.get("count", ""),
                    "normalized_count": expr.get("normalized_count", ""),
                    "signature_tier": hit["signature_tier"],
                    "signature_category": hit["signature_category"],
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
