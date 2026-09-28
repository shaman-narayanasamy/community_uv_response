rule match_uv_signatures:
    input:
        annotations = annotation_table,
        signatures = signature_table,
    output:
        hits = "uv_signature_hits.tsv",
        entity_summary = "uv_signature_entity_summary.tsv",
    log:
        "logs/uv_signature/match_uv_signatures.log",
    shell:
        """
        mkdir -p $(dirname {log})
        {PYTHON} {REPO_ROOT}/scripts/match_uv_signatures.py \
          --annotations {input.annotations} \
          --signatures {input.signatures} \
          --hits-output {output.hits} \
          --entity-summary-output {output.entity_summary} \
          > {log} 2>&1
        """
