#!/usr/bin/env python
"""Join bedtools gene coverage files to UV signature hits."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


RUN_COLUMNS = (
    "entity_type",
    "entity_id",
    "MAG_ID",
    "gene_id",
    "sample_id",
    "run_id",
    "data_type",
    "condition",
    "phase",
    "cycle",
    "analysis_group",
    "comparison_group",
    "raw_count",
    "covered_bases",
    "gene_length",
    "breadth",
    "signature_tier",
    "signature_category",
    "signature_gene_symbol",
)
SUMMARY_COLUMNS = (
    "entity_type",
    "entity_id",
    "MAG_ID",
    "gene_id",
    "sample_id",
    "data_type",
    "condition",
    "cycle",
    "comparison_group",
    "raw_count",
    "covered_bases",
    "gene_length",
    "breadth",
    "n_runs",
    "signature_tier",
    "signature_category",
    "signature_gene_symbol",
)
BEDTOOLS_COLUMNS = (
    "contig",
    "start",
    "end",
    "gene_id",
    "score",
    "strand",
    "raw_count",
    "covered_bases",
    "gene_length",
    "breadth",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def read_coverage(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        first = handle.readline()
        if not first:
            return []
        handle.seek(0)
        if first.rstrip("\n").split("\t")[0] in {"contig", "chrom", "seqid"}:
            reader = csv.DictReader(handle, delimiter="\t")
        else:
            reader = csv.DictReader(handle, fieldnames=BEDTOOLS_COLUMNS, delimiter="\t")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def sample_id(row: dict[str, str]) -> str:
    return row.get("sample_id") or row.get("sample_alias") or ""


def comparison_group(row: dict[str, str]) -> str:
    condition = row.get("condition", "")
    cycle = row.get("cycle", "")
    if condition and cycle:
        return f"{condition}_cycle{cycle}"
    return row.get("analysis_group", "")


def number(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6g}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hits", required=True, type=Path)
    parser.add_argument("--coverage-manifest", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--run-output", required=True, type=Path)
    parser.add_argument("--sample-summary-output", required=True, type=Path)
    args = parser.parse_args()

    hits = read_tsv(args.hits)
    manifest = read_tsv(args.coverage_manifest)
    metadata = read_tsv(args.metadata)
    hits_by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    for hit in hits:
        hits_by_gene[hit["gene_id"]].append(hit)

    metadata_by_sample = {sample_id(row): row for row in metadata}
    run_rows = []
    for item in manifest:
        path = Path(item["path"])
        sid = sample_id(item)
        meta = metadata_by_sample.get(sid, {})
        for cov in read_coverage(path):
            for hit in hits_by_gene.get(cov.get("gene_id", ""), []):
                run_rows.append(
                    {
                        "entity_type": hit.get("entity_type", "MAG"),
                        "entity_id": hit.get("entity_id") or hit.get("MAG_ID", ""),
                        "MAG_ID": hit.get("MAG_ID") or hit.get("entity_id", ""),
                        "gene_id": hit["gene_id"],
                        "sample_id": sid,
                        "run_id": item.get("run_id", path.stem),
                        "data_type": item.get("data_type", ""),
                        "condition": meta.get("condition", ""),
                        "phase": meta.get("phase", ""),
                        "cycle": meta.get("cycle", ""),
                        "analysis_group": meta.get("analysis_group", ""),
                        "comparison_group": comparison_group(meta),
                        "raw_count": cov.get("raw_count") or cov.get("count", "0"),
                        "covered_bases": cov.get("covered_bases", "0"),
                        "gene_length": cov.get("gene_length", "0"),
                        "breadth": cov.get("breadth", ""),
                        "signature_tier": hit["signature_tier"],
                        "signature_category": hit["signature_category"],
                        "signature_gene_symbol": hit["signature_gene_symbol"],
                    }
                )

    grouped: dict[tuple[str, ...], dict[str, float | set[str]]] = defaultdict(
        lambda: {"raw_count": 0.0, "covered_bases": 0.0, "gene_length": 0.0, "runs": set()}
    )
    for row in run_rows:
        key = (
            row["entity_type"],
            row["entity_id"],
            row["MAG_ID"],
            row["gene_id"],
            row["sample_id"],
            row["data_type"],
            row["condition"],
            row["cycle"],
            row["comparison_group"],
            row["signature_tier"],
            row["signature_category"],
            row["signature_gene_symbol"],
        )
        grouped[key]["raw_count"] += number(row["raw_count"])
        grouped[key]["covered_bases"] += number(row["covered_bases"])
        grouped[key]["gene_length"] = max(grouped[key]["gene_length"], number(row["gene_length"]))
        grouped[key]["runs"].add(row["run_id"])

    summary_rows = []
    for key, values in sorted(grouped.items()):
        gene_length = values["gene_length"]
        covered_bases = values["covered_bases"]
        breadth = covered_bases / gene_length if gene_length else 0.0
        summary_rows.append(
            dict(
                zip(
                    SUMMARY_COLUMNS,
                    (
                        key[0],
                        key[1],
                        key[2],
                        key[3],
                        key[4],
                        key[5],
                        key[6],
                        key[7],
                        key[8],
                        format_number(values["raw_count"]),
                        format_number(covered_bases),
                        format_number(gene_length),
                        f"{breadth:.7f}",
                        len(values["runs"]),
                        key[9],
                        key[10],
                        key[11],
                    ),
                )
            )
        )

    for path, rows, columns in (
        (args.run_output, run_rows, RUN_COLUMNS),
        (args.sample_summary_output, summary_rows, SUMMARY_COLUMNS),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
