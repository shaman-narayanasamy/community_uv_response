# Output contract

This file defines the planned stable outputs for downstream analysis repositories.

## UV signature tables

`uv_signature_hits.tsv`

- `MAG_ID`
- `gene_id`
- `gene_symbol`
- `gene_function`
- `signature_tier`
- `signature_category`
- `signature_gene_symbol`
- `match_type`: `gene_symbol`, `synonym`, or `product_regex`

`uv_signature_mag_summary.tsv`

- `MAG_ID`
- `signature_tier`
- `signature_category`
- `n_signature_genes`
- `n_unique_signature_symbols`

`uv_signature_expression_summary.tsv`

- `MAG_ID`
- `gene_id`
- `sample_id`
- `condition`
- `phase`
- `cycle`
- `analysis_group`
- `raw_count`
- `normalized_count`
- `signature_tier`
- `signature_category`

## inStrain summary tables

`instrain_profile_manifest.tsv`

- `sample_id`
- `bam_path`
- `profile_dir`
- `status`: `ready` when the BAM exists, otherwise `missing_bam`
- `notes`

`instrain_compare_summary.tsv`

- `genome`
- `sample_a`
- `sample_b`
- `condition_a`
- `condition_b`
- `cycle_a`
- `cycle_b`
- `coverage_status`
- `popANI`
- `compared_bases_count`
- `SNV_distance`

`rmag_snv_divergence.tsv`

- `MAG_ID`
- `comparison_axis`
- `comparison_label`
- `n_valid_pairs`
- `mean_snv_distance`
- `mean_popani`
- `interpretation_status`: currently `strain_divergence_summary`
