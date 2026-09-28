import csv
import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(workflow.basedir, ".."))
CONFIG = os.environ.get("CONFIG", os.path.join(REPO_ROOT, "config", "config.yml"))
PYTHON = sys.executable

configfile: CONFIG


output_dir = config["output_dir"]


def repo_relative(path):
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


signature_table = repo_relative(
    config.get("signature_table", os.path.join("resources", "uv_resistance_signatures.tsv"))
)
annotation_table = repo_relative(config["annotation_table"])
sample_metadata = repo_relative(config["sample_metadata"])
bam_manifest = repo_relative(config["bam_manifest"])
profile_root = config.get("instrain", {}).get("profile_root", os.path.join(output_dir, "instrain", "profiles"))
run_instrain = config.get("instrain", {}).get("run_profiles", False)
instrain_compare_table = config.get("instrain", {}).get("compare_table")
instrain_compare_table = repo_relative(instrain_compare_table) if instrain_compare_table else None
expression_counts = config.get("expression_counts")
expression_counts = repo_relative(expression_counts) if expression_counts else None
gene_coverage_manifest = config.get("gene_coverage_manifest")
gene_coverage_manifest = repo_relative(gene_coverage_manifest) if gene_coverage_manifest else None


def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


metadata_rows = read_tsv(sample_metadata)
sample_ids = [row.get("sample_id") or row.get("sample_alias") for row in metadata_rows]
bam_by_sample = {row["sample_id"]: row["bam_path"] for row in read_tsv(bam_manifest)}


uv_outputs = ["uv_signature_hits.tsv", "uv_signature_entity_summary.tsv", "instrain_profile_manifest.tsv"]

if expression_counts:
    uv_outputs.append("uv_signature_expression_summary.tsv")

if gene_coverage_manifest:
    uv_outputs.extend([
        "uv_signature_gene_coverage_run_level.tsv",
        "uv_signature_gene_coverage_sample_summary.tsv",
    ])

if instrain_compare_table:
    uv_outputs.extend(["instrain_compare_summary.tsv", "rmag_snv_divergence.tsv"])

if run_instrain:
    uv_outputs.append(os.path.join("instrain", "compare", "all_samples", "compare.done"))


workdir:
    output_dir


include:
    "../rules/uv_signature/signatures.smk"

include:
    "../rules/expression/expression.smk"

include:
    "../rules/instrain/instrain.smk"


rule all:
    input:
        uv_outputs
