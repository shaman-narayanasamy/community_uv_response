# community_uv_response

Reusable UV/DNA-damage signature and inStrain SNV module for microbial community and rMAG analyses.

This repository is intentionally dataset-agnostic. It accepts dereplicated MAG FASTA files, metagenomic read mappings, gene annotations, UV/DNA-damage signature definitions, and sample metadata, then produces reusable tables for downstream manuscript or comparative analyses. Phage-host ecology can be integrated downstream, but this module tracks community-level UV/DNA-damage response and strain divergence rather than UV resistance in phages.

## Current scope

- Map gene annotations to curated UV/DNA-damage resistance signatures.
- Run or wrap inStrain profiles from metagenomic BAMs mapped to dereplicated MAGs.
- Summarize rMAG-level SNV divergence and microdiversity with explicit coverage/breadth thresholds.
- Export stable TSV outputs that downstream analysis repos can consume.

## Inputs

Expected inputs are provided by a project-specific manifest or config:

- dereplicated rMAG FASTA file
- per-sample metagenomic BAMs mapped to the rMAG FASTA
- sample metadata with `sample_id`, `condition`, `phase`, `cycle`, and optional `analysis_group`
- gene annotation table with `MAG_ID`, `gene_id`, `gene_symbol`, and `gene_function`
- UV/DNA-damage signature table, defaulting to `resources/uv_resistance_signatures.tsv`

## Outputs

Planned stable outputs:

- `uv_signature_hits.tsv`
- `uv_signature_mag_summary.tsv`
- `uv_signature_expression_summary.tsv`
- `instrain_profile_manifest.tsv`
- `instrain_compare_summary.tsv`
- `rmag_snv_divergence.tsv`

## Interpretation guardrails

SNV results should be interpreted as strain-level divergence or microdiversity under experimental conditions. They should not be described as direct evidence that UV caused specific mutations without additional validation.

## HPC Codex handoff

When working directly on the HPC, start with `docs/hpc_codex_handoff.md`. It records the current branch, scope, expected upstream outputs, first smoke tests, and the next implementation targets so a Codex session on the cluster does not need this chat context.
