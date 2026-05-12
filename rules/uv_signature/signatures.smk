rule match_uv_signatures:
    input:
        annotations = annotation_table,
        signatures = signature_table,
    output:
        hits = "uv_signature_hits.tsv",
        mag_summary = "uv_signature_mag_summary.tsv",
    log:
        "logs/uv_signature/match_uv_signatures.log",
    shell:
        """
        mkdir -p $(dirname {log})
        python {REPO_ROOT}/scripts/match_uv_signatures.py \
          --annotations {input.annotations} \
          --signatures {input.signatures} \
          --hits-output {output.hits} \
          --mag-summary-output {output.mag_summary} \
          > {log} 2>&1
        """
