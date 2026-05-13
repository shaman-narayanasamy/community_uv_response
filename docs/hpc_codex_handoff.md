# HPC Codex handoff

This document is for Codex sessions running directly on the HPC. It is the minimum context needed to continue testing and implementing `community_uv_response` close to the data.

## Repository

- GitHub: `git@github.com:shaman-narayanasamy/community_uv_response.git`
- Current integration branch: `dev`
- Current working PR branch: `feature/community-uv-snakemake-module`
- Open draft PR: `https://github.com/shaman-narayanasamy/community_uv_response/pull/7`
- Latest implementation commit: `91b5672 Add community UV Snakemake module`
- Old repo name: `phage_uv_resistance`; GitHub redirects should work, but new work should use `community_uv_response`.

Clone or update on HPC:

```sh
mkdir -p ~/repositories/github
cd ~/repositories/github
git clone git@github.com:shaman-narayanasamy/community_uv_response.git
cd community_uv_response
git switch feature/community-uv-snakemake-module
git pull --ff-only
```

## Current PRJEB79569 state on HPC

The reusable module is implemented and pushed in draft PR #7. A local ignored
config was created at `config/local_PRJEB79569.yml` in the working checkout; it
is intentionally not committed because it contains scratch paths.

The generated project BAM manifest is:

```text
/scratch/users/snarayanasamy/phage_uv_treatment/metadata/rmag_metagenomic_bams.tsv
```

It maps the 12 biological sample IDs from
`/scratch/users/snarayanasamy/phage_uv_treatment/metadata/PRJEB79569_binning_input.tsv`
to expected upstream binning BAM paths like:

```text
/scratch/users/snarayanasamy/phage_uv_treatment/output/PRJEB79569/binning/CBF1/CBF1_metaG.reads.sorted.bam
```

The real PRJEB79569 dry-run currently blocks on a missing normalized annotation
table:

```text
/scratch/users/snarayanasamy/phage_uv_treatment/metadata/rmag_gene_annotations.tsv
```

Once upstream Bakta outputs exist under the multiomics annotation output,
normalize them with:

```sh
python scripts/prepare_bakta_annotations.py \
  --bakta-root /scratch/users/snarayanasamy/phage_uv_treatment/output/PRJEB79569/annotation/bakta \
  --output /scratch/users/snarayanasamy/phage_uv_treatment/metadata/rmag_gene_annotations.tsv
```

Then retry:

```sh
conda run -n snakemake_env snakemake \
  --snakefile workflows/community_uv_response.smk \
  --configfile config/local_PRJEB79569.yml \
  --cores 1 \
  --dry-run
```

## Scientific scope

This module is for microbial community and rMAG-level UV/DNA-damage response, not phage UV resistance. It should consume outputs from the running multi-omics and phage-host pipelines, then produce stable tables for the manuscript analysis repository.

Use metagenomic read mappings for SNV/inStrain work. Do not use metatranscriptomic reads for SNV calling.

## Upstream outputs expected from running pipelines

From `multiomics_pipeline`:

- dereplicated rMAG FASTA file
- rMAG quality/taxonomy table
- Bakta or equivalent annotation tables
- metagenomic BAMs mapped to dereplicated rMAGs, or enough data to produce them
- sample metadata resolving `sample_id`, `condition`, `phase`, `cycle`, and `analysis_group`
- optional metatranscriptomic gene counts for expression summaries

From `host_phage_linking`:

- vOTU/phage summary tables
- CRISPR spacer-protospacer links
- host-phage network table or equivalent rMAG/phage link table

## Current scaffold contents

- `resources/uv_resistance_signatures.tsv`: curated UV/DNA-damage signature definitions.
- `scripts/validate_uv_signatures.R`: validates the signature TSV schema.
- `scripts/match_uv_signatures.py`: maps annotations to signature hits and MAG summaries.
- `scripts/prepare_bakta_annotations.py`: normalizes Bakta TSVs into the required annotation table.
- `scripts/prepare_bam_manifest.py`: creates a BAM manifest from metadata and a configured BAM path pattern.
- `scripts/summarize_uv_expression.py`: optionally joins long-format expression counts to UV hits.
- `scripts/generate_instrain_manifest.py`: builds the inStrain profile manifest from metadata and BAM paths.
- `scripts/parse_instrain_compare.py`: normalizes fixture-backed inStrain compare summaries.
- `scripts/run_instrain_hpc_template.sh`: template for running inStrain profiles/compare from rMAG BAMs.
- `workflows/community_uv_response.smk`: main reusable Snakemake entrypoint.
- `config/examples/PRJEB79569_config.yml`: placeholder config shaped for the current project.
- `tests/run_fixture_tests.sh`: exact-output regression tests using tiny TSV fixtures.
- `docs/output_contract.md`: planned output table contracts.

## First smoke tests on HPC

Run these before implementing against large data:

```sh
bash -n scripts/run_instrain_hpc_template.sh
python -m py_compile scripts/*.py
bash tests/run_fixture_tests.sh
conda run -n snakemake_env snakemake \
  --snakefile workflows/community_uv_response.smk \
  --configfile config/examples/fixture_config.yml \
  --cores 1 \
  --dry-run \
  --forceall
```

`Rscript scripts/validate_uv_signatures.R resources/uv_resistance_signatures.tsv`
is also useful when `Rscript` is available; it was not available in the shell
used for PR #7.

## Recommended next implementation order

1. Wait for upstream multiomics binning/annotation outputs to finish.
2. Normalize Bakta TSVs into `rmag_gene_annotations.tsv`.
3. Re-run the real PRJEB79569 Snakemake dry-run with `config/local_PRJEB79569.yml`.
4. Inspect `uv_signature_hits.tsv` and `uv_signature_mag_summary.tsv` before running inStrain.
5. Validate inStrain profile execution on one or two metagenomic BAMs before enabling all samples.
6. Replace fixture-backed compare input with real inStrain comparison summaries once available.

## Interpretation guardrails

- Tier 1 signatures are direct UV lesion repair or nucleotide excision repair.
- Tier 2 signatures are DNA-damage response and recombination repair context.
- Tier 3 signatures are supportive oxidative/redox/general stress context.
- SNV patterns should be described as strain-level divergence or microdiversity under repeated treatment.
- Do not claim UV-caused mutations from inStrain comparisons alone.

## Notes for Codex on HPC

- Prefer small fixtures and dry-runs before using full PRJEB79569 data.
- Keep project-specific paths in the project analysis repository or HPC config, not in this reusable module.
- If a script needs an HPC path, pass it as an argument or environment variable.
- Commit reusable code here; keep run logs, large outputs, BAMs, FASTQs, and derived bulk tables out of git.
