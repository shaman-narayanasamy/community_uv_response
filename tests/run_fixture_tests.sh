#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${TMP_DIR:-/tmp/community_uv_response_test}"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

python "$ROOT/scripts/match_uv_signatures.py" \
  --annotations "$ROOT/tests/fixtures/annotations.tsv" \
  --signatures "$ROOT/tests/fixtures/signatures.tsv" \
  --hits-output "$TMP_DIR/uv_signature_hits.tsv" \
  --mag-summary-output "$TMP_DIR/uv_signature_mag_summary.tsv"

python "$ROOT/scripts/prepare_bakta_annotations.py" \
  --bakta-root "$ROOT/tests/fixtures/bakta" \
  --output "$TMP_DIR/prepared_bakta_annotations.tsv"

python "$ROOT/scripts/prepare_bam_manifest.py" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --sample-column sample_alias \
  --bam-pattern "/tmp/community_uv_response_bams/{sample_id}/{sample_id}.rmag.bam" \
  --output "$TMP_DIR/prepared_bam_manifest.tsv"

python "$ROOT/scripts/summarize_uv_expression.py" \
  --hits "$TMP_DIR/uv_signature_hits.tsv" \
  --expression "$ROOT/tests/fixtures/expression_counts.tsv" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --output "$TMP_DIR/uv_signature_expression_summary.tsv"

python "$ROOT/scripts/generate_instrain_manifest.py" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --bam-manifest "$ROOT/tests/fixtures/bam_manifest.tsv" \
  --profile-root "$TMP_DIR/profiles" \
  --output "$TMP_DIR/instrain_profile_manifest.tsv"

python "$ROOT/scripts/parse_instrain_compare.py" \
  --compare-table "$ROOT/tests/fixtures/instrain_compare.tsv" \
  --metadata "$ROOT/tests/fixtures/metadata.tsv" \
  --compare-summary-output "$TMP_DIR/instrain_compare_summary.tsv" \
  --rmag-output "$TMP_DIR/rmag_snv_divergence.tsv"

for name in \
  uv_signature_hits.tsv \
  uv_signature_mag_summary.tsv \
  uv_signature_expression_summary.tsv \
  instrain_profile_manifest.tsv \
  instrain_compare_summary.tsv \
  rmag_snv_divergence.tsv \
  prepared_bakta_annotations.tsv \
  prepared_bam_manifest.tsv
do
  diff -u "$ROOT/tests/fixtures/expected/$name" "$TMP_DIR/$name"
done

echo "Fixture tests passed."
