# Community UV response

Tools for matching microbial gene annotations to UV/DNA-damage signatures
and summarising inStrain population-genomic comparisons.

## Inputs

- Dereplicated MAG FASTA files and sample-specific metagenomic BAMs.
- Sample metadata with `sample_id`, `condition`, `phase` and `cycle`.
- Gene annotations with `entity_type`, `entity_id`, `gene_id`, `gene_symbol`
  and `gene_function`. Legacy `MAG_ID` tables are also accepted.
- Signature definitions, supplied in `resources/uv_resistance_signatures.tsv`.
- Optional gene-coverage and inStrain comparison tables.

Input helpers under `scripts/` prepare Bakta and Cenote-Taker annotations,
BAM manifests and gene-coverage manifests. The Bakta helper records duplicate
annotations and accepts `--fail-on-conflicts`.

## Running the workflow

Copy `config/examples/PRJEB79569_config.yml`, replace its paths and save the
configuration as an ignored local file:

```sh
snakemake --snakefile workflows/community_uv_response.smk \
  --configfile config/local_PRJEB79569.yml --cores 16 --dry-run
```

Set `instrain.run_profiles: true` when the BAMs, reference FASTA and inStrain
installation are available. Otherwise the workflow can prepare manifests and
summarise supplied comparison tables.

## Outputs

Signature outputs include `uv_signature_hits.tsv` and
`uv_signature_entity_summary.tsv`. Optional expression and gene-coverage
inputs produce corresponding summary tables. Population-genomic outputs
include `instrain_profile_manifest.tsv`, `instrain_compare_summary.tsv` and
`rmag_snv_divergence.tsv`.

Run the local fixture tests with:

```sh
bash tests/run_fixture_tests.sh
```

## PRJEB79569 analysis

This module supplies annotations and descriptive population-genomic tables to
[phage_uv_ecology_analysis](https://github.com/shaman-narayanasamy/phage_uv_ecology_analysis).
Raw data: https://www.ebi.ac.uk/ena/browser/view/PRJEB79569.
Transcriptome-wide statistical testing is performed in the analysis repository.
