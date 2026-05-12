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
- `scripts/run_instrain_hpc_template.sh`: template for running inStrain profiles/compare from rMAG BAMs.
- `docs/output_contract.md`: planned output table contracts.

## First smoke tests on HPC

Run these before implementing against large data:

```sh
Rscript scripts/validate_uv_signatures.R resources/uv_resistance_signatures.tsv
bash -n scripts/run_instrain_hpc_template.sh
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

1. Implement annotation-to-UV-signature matching.
2. Add a tiny fixture annotation table and expected outputs.
3. Add command-line validation for required input columns.
4. Implement rMAG-level UV signature summaries.
5. Implement inStrain profile manifest generation from sample metadata and BAM paths.
6. Add inStrain compare summary parsing only after real profile/compare outputs exist.

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
