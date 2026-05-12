# HPC Codex handoff

This document is for Codex sessions running directly on the HPC. It is the minimum context needed to continue testing and implementing `community_uv_response` close to the data.

## Repository

- GitHub: `git@github.com:shaman-narayanasamy/community_uv_response.git`
- Current integration branch: `dev`
- Current working PR branch: `feature/initial-uv-module-scaffold`
- Open PR: `https://github.com/shaman-narayanasamy/community_uv_response/pull/6`
- Old repo name: `phage_uv_resistance`; GitHub redirects should work, but new work should use `community_uv_response`.

Clone or update on HPC:

```sh
mkdir -p ~/repositories/github
cd ~/repositories/github
git clone git@github.com:shaman-narayanasamy/community_uv_response.git
cd community_uv_response
git switch feature/initial-uv-module-scaffold
git pull --ff-only
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
Rscript scripts/validate_uv_signatures.R resources/uv_resistance_signatures.tsv
bash -n scripts/run_instrain_hpc_template.sh
bash tests/run_fixture_tests.sh
snakemake --snakefile workflows/community_uv_response.smk \
  --configfile config/local_PRJEB79569.yml \
  --cores 16 \
  --dry-run
```

Then create a tiny temporary annotation table with columns:

```text
MAG_ID	gene_id	gene_symbol	gene_function
```

Use it to develop and test the first real executable target:

```text
annotation table + resources/uv_resistance_signatures.tsv
  -> uv_signature_hits.tsv
  -> uv_signature_mag_summary.tsv
```

## Recommended next implementation order

1. Create an ignored local config from `config/examples/PRJEB79569_config.yml`.
2. Run the fixture tests and Snakemake dry-run on the HPC environment.
3. Point the config at real multiomics annotation, metadata, BAM manifest, and rMAG FASTA paths.
4. Validate inStrain profile execution on one or two metagenomic BAMs before enabling all samples.
5. Replace fixture-backed compare input with real inStrain comparison summaries once available.

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
