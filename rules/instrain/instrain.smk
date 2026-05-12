rule generate_instrain_manifest:
    input:
        metadata = sample_metadata,
        bam_manifest = bam_manifest,
    output:
        "instrain_profile_manifest.tsv",
    log:
        "logs/instrain/generate_manifest.log",
    shell:
        """
        mkdir -p $(dirname {log})
        python {REPO_ROOT}/scripts/generate_instrain_manifest.py \
          --metadata {input.metadata} \
          --bam-manifest {input.bam_manifest} \
          --profile-root {profile_root} \
          --output {output} \
          > {log} 2>&1
        """


rule instrain_profile:
    input:
        fasta = lambda wildcards: config["rmag_fasta"],
        bam = lambda wildcards: bam_by_sample[wildcards.sample],
    output:
        done = touch("instrain/profiles/{sample}/profile.done"),
    params:
        out_dir = "instrain/profiles/{sample}",
    threads:
        config.get("instrain", {}).get("threads", 16)
    log:
        "logs/instrain/profile/{sample}.log",
    shell:
        """
        mkdir -p $(dirname {log}) {params.out_dir}
        inStrain profile {input.bam} {input.fasta} -o {params.out_dir} -p {threads} > {log} 2>&1
        """


rule instrain_compare:
    input:
        profiles = expand("instrain/profiles/{sample}/profile.done", sample=sample_ids),
    output:
        done = touch("instrain/compare/all_samples/compare.done"),
    params:
        profile_dirs = expand("instrain/profiles/{sample}", sample=sample_ids),
        out_dir = "instrain/compare/all_samples",
    threads:
        config.get("instrain", {}).get("threads", 16)
    log:
        "logs/instrain/compare/all_samples.log",
    shell:
        """
        mkdir -p $(dirname {log}) {params.out_dir}
        inStrain compare -i {params.profile_dirs} -o {params.out_dir} -p {threads} > {log} 2>&1
        """


if instrain_compare_table:
    rule parse_instrain_compare:
        input:
            compare_table = instrain_compare_table,
            metadata = sample_metadata,
        output:
            compare_summary = "instrain_compare_summary.tsv",
            rmag_divergence = "rmag_snv_divergence.tsv",
        log:
            "logs/instrain/parse_compare.log",
        shell:
            """
            mkdir -p $(dirname {log})
            python {REPO_ROOT}/scripts/parse_instrain_compare.py \
              --compare-table {input.compare_table} \
              --metadata {input.metadata} \
              --compare-summary-output {output.compare_summary} \
              --rmag-output {output.rmag_divergence} \
              > {log} 2>&1
            """
