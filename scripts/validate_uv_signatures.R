#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
signature_path <- if (length(args) >= 1) args[[1]] else "resources/uv_resistance_signatures.tsv"

if (!requireNamespace("readr", quietly = TRUE)) {
  stop("Package 'readr' is required.")
}

sig <- readr::read_tsv(signature_path, show_col_types = FALSE)
required <- c("tier", "category", "gene_symbol", "synonyms", "product_regex", "specificity", "rationale")
missing <- setdiff(required, names(sig))

if (length(missing) > 0) {
  stop("Missing required columns: ", paste(missing, collapse = ", "))
}

if (!all(sig$tier %in% c(1, 2, 3, "1", "2", "3"))) {
  stop("UV signature tiers must be 1, 2, or 3.")
}

if (any(is.na(sig$gene_symbol) | sig$gene_symbol == "")) {
  stop("All UV signature rows must define gene_symbol.")
}

message("Validated ", nrow(sig), " UV signature rows from ", signature_path)

