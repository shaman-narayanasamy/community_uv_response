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
            python {REPO_ROOT}/scripts/summarize_uv_expression.py \
              --hits {input.hits} \
              --expression {input.expression} \
              --metadata {input.metadata} \
              --output {output} \
              > {log} 2>&1
            """
