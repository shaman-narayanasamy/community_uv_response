#!/usr/bin/env python
"""Create an inStrain profile manifest from sample metadata and BAM paths."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = ("sample_id", "bam_path", "profile_dir", "status", "notes")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def sample_id(row: dict[str, str]) -> str:
    return row.get("sample_id") or row.get("sample_alias") or ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--bam-manifest", required=True, type=Path)
    parser.add_argument("--profile-root", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    metadata = read_tsv(args.metadata)
    bam_manifest = read_tsv(args.bam_manifest)
    if bam_manifest and "sample_id" not in bam_manifest[0]:
        raise SystemExit(f"{args.bam_manifest} missing required column: sample_id")
    if bam_manifest and "bam_path" not in bam_manifest[0]:
        raise SystemExit(f"{args.bam_manifest} missing required column: bam_path")

    bam_by_sample = {row["sample_id"]: row["bam_path"] for row in bam_manifest}
    rows = []
    for meta in metadata:
        sid = sample_id(meta)
        if not sid:
            raise SystemExit(f"{args.metadata} has a row without sample_id or sample_alias")
        bam_path = bam_by_sample.get(sid, "")
        status = "ready" if bam_path and Path(bam_path).exists() else "missing_bam"
        notes = "" if status == "ready" else "BAM path is missing or does not exist"
        rows.append(
            {
                "sample_id": sid,
                "bam_path": bam_path,
                "profile_dir": str(Path(args.profile_root) / sid),
                "status": status,
                "notes": notes,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, OUTPUT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
