#!/usr/bin/env python
"""Map gene annotations to curated UV/DNA-damage signatures."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


ANNOTATION_COLUMNS = ("gene_id", "gene_symbol", "gene_function")
SIGNATURE_COLUMNS = (
    "tier",
    "category",
    "gene_symbol",
    "synonyms",
    "product_regex",
    "specificity",
    "rationale",
)
HIT_COLUMNS = (
    "entity_type",
    "entity_id",
    "MAG_ID",
    "gene_id",
    "gene_symbol",
    "gene_function",
    "signature_tier",
    "signature_category",
    "signature_gene_symbol",
    "match_type",
)
SUMMARY_COLUMNS = (
    "entity_type",
    "entity_id",
    "MAG_ID",
    "signature_tier",
    "signature_category",
    "n_signature_genes",
    "n_unique_signature_symbols",
)


def read_tsv(
    path: Path, required_columns: tuple[str, ...], require_entity: bool = False
) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"{path} is empty or missing a header")
        missing = [column for column in required_columns if column not in reader.fieldnames]
        if missing:
            raise SystemExit(f"{path} missing required columns: {', '.join(missing)}")
        if require_entity and "entity_id" not in reader.fieldnames and "MAG_ID" not in reader.fieldnames:
            raise SystemExit(f"{path} missing required entity column: entity_id or MAG_ID")
        return [{key: (value or "") for key, value in row.items()} for row in reader]


def write_tsv(path: Path, rows: list[dict[str, object]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str) -> str:
    return value.strip().lower()


def entity_id(annotation: dict[str, str]) -> str:
    return annotation.get("entity_id") or annotation.get("MAG_ID", "")


def entity_type(annotation: dict[str, str]) -> str:
    return annotation.get("entity_type") or "MAG"


def signature_aliases(signature: dict[str, str]) -> set[str]:
    aliases = {normalize(signature["gene_symbol"])}
    aliases.update(normalize(item) for item in signature.get("synonyms", "").split(";") if item.strip())
    return {alias for alias in aliases if alias}


def compile_product_patterns(product_regex: str) -> list[re.Pattern[str]]:
    patterns = []
    for alternative in product_regex.split("|"):
        alternative = alternative.strip()
        if not alternative:
            continue
        if re.fullmatch(r"[A-Za-z0-9_]+", alternative):
            pattern = rf"\b{re.escape(alternative)}\b"
        else:
            pattern = alternative
        patterns.append(re.compile(pattern, re.IGNORECASE))
    return patterns


def prepare_signatures(signatures: list[dict[str, str]]) -> None:
    for signature in signatures:
        signature["_product_patterns"] = compile_product_patterns(signature.get("product_regex", ""))


def product_regex_matches(signature: dict[str, str], gene_function: str) -> bool:
    return any(pattern.search(gene_function) for pattern in signature.get("_product_patterns", []))


def best_match(annotation: dict[str, str], signature: dict[str, str]) -> str | None:
    gene_symbol = normalize(annotation.get("gene_symbol", ""))
    aliases = signature_aliases(signature)
    if gene_symbol and gene_symbol == normalize(signature["gene_symbol"]):
        return "gene_symbol"
    if gene_symbol and gene_symbol in aliases:
        return "synonym"

    gene_function = annotation.get("gene_function", "")
    if gene_function and product_regex_matches(signature, gene_function):
        return "product_regex"
    return None


def build_hits(
    annotations: list[dict[str, str]], signatures: list[dict[str, str]]
) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for annotation in annotations:
        eid = entity_id(annotation)
        etype = entity_type(annotation)
        for signature in signatures:
            match_type = best_match(annotation, signature)
            if match_type is None:
                continue
            hits.append(
                {
                    "entity_type": etype,
                    "entity_id": eid,
                    "MAG_ID": annotation.get("MAG_ID") or eid,
                    "gene_id": annotation["gene_id"],
                    "gene_symbol": annotation["gene_symbol"],
                    "gene_function": annotation["gene_function"],
                    "signature_tier": signature["tier"],
                    "signature_category": signature["category"],
                    "signature_gene_symbol": signature["gene_symbol"],
                    "match_type": match_type,
                }
            )
    return hits


def build_entity_summary(hits: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"genes": set(), "symbols": set()}
    )
    for hit in hits:
        key = (hit["entity_type"], hit["entity_id"], hit["signature_tier"], hit["signature_category"])
        grouped[key]["genes"].add(hit["gene_id"])
        grouped[key]["symbols"].add(hit["signature_gene_symbol"])

    rows = []
    for (etype, eid, tier, category), values in sorted(grouped.items()):
        rows.append(
            {
                "entity_type": etype,
                "entity_id": eid,
                "MAG_ID": eid,
                "signature_tier": tier,
                "signature_category": category,
                "n_signature_genes": len(values["genes"]),
                "n_unique_signature_symbols": len(values["symbols"]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--signatures", required=True, type=Path)
    parser.add_argument("--hits-output", required=True, type=Path)
    parser.add_argument("--entity-summary-output", type=Path)
    parser.add_argument("--mag-summary-output", type=Path, help="Deprecated alias for --entity-summary-output")
    args = parser.parse_args()

    summary_output = args.entity_summary_output or args.mag_summary_output
    if summary_output is None:
        raise SystemExit("Provide --entity-summary-output or --mag-summary-output")

    annotations = read_tsv(args.annotations, ANNOTATION_COLUMNS, require_entity=True)
    signatures = read_tsv(args.signatures, SIGNATURE_COLUMNS)
    prepare_signatures(signatures)
    hits = build_hits(annotations, signatures)
    write_tsv(args.hits_output, hits, HIT_COLUMNS)
    write_tsv(summary_output, build_entity_summary(hits), SUMMARY_COLUMNS)


if __name__ == "__main__":
    main()
