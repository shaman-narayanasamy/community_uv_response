if expression_counts:
    rule summarize_uv_expression:
        input:
            hits = "uv_signature_hits.tsv",
            expression = expression_counts,
            metadata = sample_metadata,
        output:
            "uv_signature_expression_summary.tsv",
        log:
            "logs/expression/summarize_uv_expression.log",
        shell:
            """
            mkdir -p $(dirname {log})
            {PYTHON} {REPO_ROOT}/scripts/summarize_uv_expression.py \
              --hits {input.hits} \
              --expression {input.expression} \
              --metadata {input.metadata} \
              --output {output} \
              > {log} 2>&1
            """

if gene_coverage_manifest:
    rule summarize_uv_gene_coverage:
        input:
            hits = "uv_signature_hits.tsv",
            manifest = gene_coverage_manifest,
            metadata = sample_metadata,
        output:
            run_level = "uv_signature_gene_coverage_run_level.tsv",
            sample_summary = "uv_signature_gene_coverage_sample_summary.tsv",
        log:
            "logs/expression/summarize_uv_gene_coverage.log",
        shell:
            """
            mkdir -p $(dirname {log})
            {PYTHON} {REPO_ROOT}/scripts/summarize_uv_gene_coverage.py \
              --hits {input.hits} \
              --coverage-manifest {input.manifest} \
              --metadata {input.metadata} \
              --run-output {output.run_level} \
              --sample-summary-output {output.sample_summary} \
              > {log} 2>&1
            """
