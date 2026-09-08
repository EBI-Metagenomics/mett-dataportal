from django.core.management.base import BaseCommand

from dataportal.ingest.feature.runner import (
    ingest_dbxref,
    ingest_essentiality,
    ingest_gff_features,
    list_ftp_isolates,
    load_assembly_mapping,
)
from dataportal.ingest.gene_experiment.runner import ingest_gene_experiments
from dataportal.utils.constants import INDEX_FEATURES, INDEX_GENE_EXPERIMENTS

_EXPERIMENT_DIR_KEYS = (
    "fitness_dir",
    "proteomics_dir",
    "protein_compound_dir",
    "pooled_ttp_dir",
    "mutant_growth_dir",
    "gene_rx_dir",
    "met_rx_dir",
    "rx_gpr_dir",
)


class Command(BaseCommand):
    help = (
        "Import annotation into feature_index (GFF, essentiality, dbxref). "
        "Gene-level assays belong in import_gene_experiments; those flags still work here."
    )

    def add_arguments(self, p):
        p.add_argument(
            "--index",
            default=INDEX_FEATURES,
            help="Target ES feature index (default: feature_index)",
        )
        p.add_argument(
            "--experiment-index",
            default=INDEX_GENE_EXPERIMENTS,
            help="Used only if gene-experiment directories are also passed",
        )

        p.add_argument("--ftp-server", default="ftp.ebi.ac.uk")
        p.add_argument("--ftp-root", default="/pub/databases/mett/annotations/v1_2024-04-15")
        p.add_argument("--isolates", nargs="*", help="If omitted, list from FTP")
        p.add_argument(
            "--mapping-task-file",
            help="Path to gff-assembly-prefixes.tsv mapping file (prefix -> assembly)",
        )
        p.add_argument(
            "--skip-core-genes",
            action="store_true",
            help="Skip importing core gene features from GFFs",
        )

        p.add_argument("--essentiality-dir", help="Folder containing essentiality CSVs")
        p.add_argument(
            "--dbxref-dir", help="Folder with TSV files for external DB mappings (e.g., STRING DB)"
        )
        p.add_argument(
            "--dbxref-db-name",
            default="STRING",
            help="Database name for dbxref entries (default: STRING)",
        )

        p.add_argument("--fitness-dir", help="Deprecated here; prefer import_gene_experiments")
        p.add_argument("--proteomics-dir", help="Deprecated here; prefer import_gene_experiments")
        p.add_argument(
            "--protein-compound-dir", help="Deprecated here; prefer import_gene_experiments"
        )
        p.add_argument("--pooled-ttp-dir", help="Deprecated here; prefer import_gene_experiments")
        p.add_argument("--pool-metadata", help="Path to pool metadata CSV file")
        p.add_argument(
            "--mutant-growth-dir", help="Deprecated here; prefer import_gene_experiments"
        )
        p.add_argument("--gene-rx-dir", help="Deprecated here; prefer import_gene_experiments")
        p.add_argument("--met-rx-dir", help="Deprecated here; prefer import_gene_experiments")
        p.add_argument("--rx-gpr-dir", help="Deprecated here; prefer import_gene_experiments")

    def handle(self, *args, **o):
        index_name = o["index"]
        mapping = load_assembly_mapping(o.get("mapping_task_file"))
        isolates = o["isolates"] or list_ftp_isolates(o["ftp_server"], o["ftp_root"])

        if not o.get("skip_core_genes"):
            ingest_gff_features(
                ftp_server=o["ftp_server"],
                ftp_root=o["ftp_root"],
                index_name=index_name,
                raw_isolates=isolates,
                mapping=mapping,
            )
        else:
            self.stdout.write("[import_features] Skipping core gene (GFF) import as requested.")

        for csv_path in ingest_essentiality(index_name, o.get("essentiality_dir")):
            self.stdout.write(f"  - {csv_path}")

        for tsv_path in ingest_dbxref(
            index_name, o.get("dbxref_dir"), o.get("dbxref_db_name", "STRING")
        ):
            self.stdout.write(f"  - {tsv_path}")

        if any(o.get(k) for k in _EXPERIMENT_DIR_KEYS):
            self.stdout.write(
                self.style.WARNING(
                    "Gene-experiment directories were passed to import_features. "
                    "Prefer: python manage.py import_gene_experiments"
                )
            )
            ingest_gene_experiments(
                experiment_index=o["experiment_index"],
                feature_index=index_name,
                fitness_dir=o.get("fitness_dir"),
                proteomics_dir=o.get("proteomics_dir"),
                protein_compound_dir=o.get("protein_compound_dir"),
                pooled_ttp_dir=o.get("pooled_ttp_dir"),
                pool_metadata=o.get("pool_metadata"),
                mutant_growth_dir=o.get("mutant_growth_dir"),
                gene_rx_dir=o.get("gene_rx_dir"),
                met_rx_dir=o.get("met_rx_dir"),
                rx_gpr_dir=o.get("rx_gpr_dir"),
            )
