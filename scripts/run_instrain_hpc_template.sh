#!/usr/bin/env bash
set -euo pipefail

# Template only: edit paths before running on HPC.
# Call variants from metagenomic read alignments.

RMAG_FASTA="${RMAG_FASTA:-/isilon/path/to/phage_uv_treatment/rMAGs/all_dereplicated_rMAGs.fa}"
SAMPLE_METADATA="${SAMPLE_METADATA:-metadata/sample_metadata.tsv}"
READ_ROOT="${READ_ROOT:-/isilon/path/to/phage_uv_treatment/reads_or_bams/metagenomics}"
OUT_ROOT="${OUT_ROOT:-/isilon/path/to/phage_uv_treatment/instrain}"
THREADS="${THREADS:-16}"

mkdir -p "${OUT_ROOT}/profiles" "${OUT_ROOT}/compare"

awk -F '\t' 'NR > 1 { print $1 "\t" $11 }' "$SAMPLE_METADATA" | while IFS=$'\t' read -r sample_title mg_run; do
  bam="${READ_ROOT}/${sample_title}.rmag.bam"
  r1="${READ_ROOT}/${mg_run}_1.fastq.gz"
  r2="${READ_ROOT}/${mg_run}_2.fastq.gz"
  profile_out="${OUT_ROOT}/profiles/${sample_title}"

  if [[ -f "$bam" ]]; then
    inStrain profile "$bam" "$RMAG_FASTA" -o "$profile_out" -p "$THREADS"
  elif [[ -f "$r1" && -f "$r2" ]]; then
    printf 'FASTQ files found for %s, but this template expects pre-mapped BAMs for inStrain profile.\n' "$sample_title" >&2
    printf 'Map reads to RMAG_FASTA first, then re-run using %s.rmag.bam.\n' "$sample_title" >&2
  else
    printf 'Missing metagenomic BAM/FASTQ for %s (%s)\n' "$sample_title" "$mg_run" >&2
  fi
done

profile_dirs=("${OUT_ROOT}"/profiles/*)
if [[ "${#profile_dirs[@]}" -gt 1 && -d "${profile_dirs[0]}" ]]; then
  inStrain compare -i "${profile_dirs[@]}" -o "${OUT_ROOT}/compare/all_samples" -p "$THREADS"
else
  printf 'Not enough inStrain profile directories for compare.\n' >&2
fi
