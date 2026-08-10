# community_uv_response

Reusable UV/DNA-damage signature and inStrain SNV module for microbial community and rMAG analyses.

This repository is intentionally dataset-agnostic. It accepts dereplicated MAG FASTA files, metagenomic read mappings, gene annotations, UV/DNA-damage signature definitions, and sample metadata, then produces reusable tables for downstream manuscript or comparative analyses. Phage-host ecology can be integrated downstream, but this module tracks community-level UV/DNA-damage response and strain divergence rather than UV resistance in phages.

For PRJEB79569, this module is an optional downstream annotation and descriptive
population-genomics component. It must not replace transcriptome-wide modeling
or be used to preselect the gene universe for differential expression.

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

Stable outputs:

- `uv_signature_hits.tsv`
- `uv_signature_mag_summary.tsv`
- `uv_signature_expression_summary.tsv` when expression counts are configured
- `instrain_profile_manifest.tsv`
- `instrain_compare_summary.tsv` when an inStrain comparison table is configured
- `rmag_snv_divergence.tsv` when an inStrain comparison table is configured

## Snakemake workflow

Copy `config/examples/PRJEB79569_config.yml`, replace the placeholder paths, and
keep real HPC paths in an ignored local config such as
`config/local_PRJEB79569.yml`.

```sh
snakemake --snakefile workflows/community_uv_response.smk \
  --configfile config/local_PRJEB79569.yml \
  --cores 16 \
  --dry-run
```

The workflow runs reusable Python transformation scripts for UV signature
matching, optional expression joins, inStrain profile manifest generation, and
fixture-backed inStrain comparison summaries. Set `instrain.run_profiles: true`
only when the configured metagenomic BAMs and rMAG FASTA are available on the
HPC and `inStrain` is on the execution path.

If upstream Bakta or BAM outputs need to be normalized first:

```sh
python scripts/prepare_bakta_annotations.py \
  --bakta-root /path/to/multiomics/output/annotation/bakta \
  --output /path/to/project/metadata/rmag_gene_annotations.tsv \
  --duplicates-output /path/to/project/metadata/rmag_gene_annotation_duplicates.tsv \
  --fail-on-conflicts

python scripts/prepare_bam_manifest.py \
  --metadata /path/to/project/metadata/PRJEB79569_multiomics_samples.tsv \
  --sample-column sample_alias \
  --bam-pattern '/path/to/rmag_bams/{sample_id}/{sample_id}.rmag.bam' \
  --output /path/to/project/metadata/rmag_metagenomic_bams.tsv
```

The Bakta normalizer reads comment-prefixed Bakta headers, accepts lowercase
`cds` feature types, and selects only primary annotation tables. Companion
`.inference.tsv` and `.hypotheticals.tsv` files are excluded. Duplicate
`MAG_ID`/`gene_id` pairs are deduplicated into the audit table; use
`--fail-on-conflicts` to prevent an annotation output when their annotations
disagree.

## Fixture tests

Run the small local regression tests with:

```sh
bash tests/run_fixture_tests.sh
```

These tests validate exact TSV outputs without requiring Snakemake, R, or
inStrain.

## Interpretation guardrails

SNV results should be interpreted as strain-level divergence or microdiversity under experimental conditions. They should not be described as direct evidence that UV caused specific mutations without additional validation.

## HPC Codex handoff

When working directly on the HPC, start with `docs/hpc_codex_handoff.md`. It records the current branch, scope, expected upstream outputs, first smoke tests, and the next implementation targets so a Codex session on the cluster does not need this chat context.
