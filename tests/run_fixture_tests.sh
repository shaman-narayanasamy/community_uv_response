#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d /tmp/community_uv_response_test.XXXXXX)"
PYTHON="${PYTHON:-python3}"


"$PYTHON" "$ROOT/scripts/match_uv_signatures.py" \
  --annotations "$ROOT/tests/fixtures/annotations.tsv" \
  --signatures "$ROOT/tests/fixtures/signatures.tsv" \
  --hits-output "$TMP_DIR/uv_signature_hits.tsv" \
  --entity-summary-output "$TMP_DIR/uv_signature_entity_summary.tsv"

"$PYTHON" "$ROOT/scripts/prepare_bakta_annotations.py" \
  --bakta-root "$ROOT/tests/fixtures/bakta" \
  --output "$TMP_DIR/prepared_bakta_annotations.tsv" \
  --duplicates-output "$TMP_DIR/prepared_bakta_duplicates.tsv"

if "$PYTHON" "$ROOT/scripts/prepare_bakta_annotations.py" \
  --bakta-root "$ROOT/tests/fixtures/bakta_conflict" \
  --output "$TMP_DIR/prepared_bakta_conflict_annotations.tsv" \
  --duplicates-output "$TMP_DIR/prepared_bakta_conflicts.tsv" \
  --fail-on-conflicts
then
  echo "Expected conflicting Bakta duplicate detection to fail" >&2
  exit 1
fi

test ! -e "$TMP_DIR/prepared_bakta_conflict_annotations.tsv"

"$PYTHON" "$ROOT/scripts/prepare_cenotetaker_annotations.py" \
  --cenote-summary "$ROOT/tests/fixtures/cenote_summary.tsv" \
  --contig-map "$ROOT/tests/fixtures/cenote_contig_map.tsv" \
  --output "$TMP_DIR/prepared_cenotetaker_annotations.tsv"

"$PYTHON" "$ROOT/scripts/combine_gene_annotations.py" \
  --annotations "$TMP_DIR/prepared_bakta_annotations.tsv" "$TMP_DIR/prepared_cenotetaker_annotations.tsv" \
  --output "$TMP_DIR/combined_gene_annotations.tsv"

"$PYTHON" "$ROOT/scripts/prepare_bam_manifest.py" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --sample-column sample_alias \
  --bam-pattern "/tmp/community_uv_response_bams/{sample_id}/{sample_id}.rmag.bam" \
  --output "$TMP_DIR/prepared_bam_manifest.tsv"

"$PYTHON" "$ROOT/scripts/summarize_uv_expression.py" \
  --hits "$TMP_DIR/uv_signature_hits.tsv" \
  --expression "$ROOT/tests/fixtures/expression_counts.tsv" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --output "$TMP_DIR/uv_signature_expression_summary.tsv"

"$PYTHON" "$ROOT/scripts/summarize_uv_gene_coverage.py" \
  --hits "$TMP_DIR/uv_signature_hits.tsv" \
  --coverage-manifest "$ROOT/tests/fixtures/gene_coverage_manifest.tsv" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --run-output "$TMP_DIR/uv_signature_gene_coverage_run_level.tsv" \
  --sample-summary-output "$TMP_DIR/uv_signature_gene_coverage_sample_summary.tsv"

"$PYTHON" "$ROOT/scripts/generate_instrain_manifest.py" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --bam-manifest "$ROOT/tests/fixtures/bam_manifest.tsv" \
  --profile-root "/tmp/community_uv_response_test/profiles" \
  --output "$TMP_DIR/instrain_profile_manifest.tsv"

"$PYTHON" "$ROOT/scripts/parse_instrain_compare.py" \
  --compare-table "$ROOT/tests/fixtures/instrain_compare.tsv" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --compare-summary-output "$TMP_DIR/instrain_compare_summary.tsv" \
  --rmag-output "$TMP_DIR/rmag_snv_divergence.tsv"

for name in \
  uv_signature_hits.tsv \
  uv_signature_entity_summary.tsv \
  uv_signature_expression_summary.tsv \
  uv_signature_gene_coverage_run_level.tsv \
  uv_signature_gene_coverage_sample_summary.tsv \
  instrain_profile_manifest.tsv \
  instrain_compare_summary.tsv \
  rmag_snv_divergence.tsv \
  prepared_bakta_annotations.tsv \
  prepared_cenotetaker_annotations.tsv \
  combined_gene_annotations.tsv \
  prepared_bakta_duplicates.tsv \
  prepared_bakta_conflicts.tsv \
  prepared_bam_manifest.tsv
do
  diff -u "$ROOT/tests/fixtures/expected/$name" "$TMP_DIR/$name"
done

echo "Fixture tests passed. Outputs: $TMP_DIR"
