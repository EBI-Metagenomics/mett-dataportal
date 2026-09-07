from django.core.management.base import BaseCommand

from dataportal.ingest.gene_experiment.runner import ingest_gene_experiments
from dataportal.utils.constants import INDEX_FEATURES, INDEX_GENE_EXPERIMENTS


class Command(BaseCommand):
    help = (
        "Import gene-level assays into gene_experiment_index "
        "(fitness, proteomics, TPP, reactions, mutant growth) and set has_* flags on features."
    )

    def add_arguments(self, p):
        p.add_argument(
            "--experiment-index",
            default=INDEX_GENE_EXPERIMENTS,
            help="Target ES gene experiment index",
        )
        p.add_argument(
            "--feature-index",
            default=INDEX_FEATURES,
            help="Feature index for denormalized has_* flags",
        )
        p.add_argument("--fitness-dir", help="Folder containing fitness CSVs")
        p.add_argument("--proteomics-dir", help="Folder containing proteomics CSVs")
        p.add_argument("--protein-compound-dir", help="Folder with protein-compound CSVs")
        p.add_argument("--pooled-ttp-dir", help="Folder with pooled TTP CSVs")
        p.add_argument("--pool-metadata", help="Path to pool metadata CSV file")
        p.add_argument("--mutant-growth-dir", help="Folder with mutant growth CSVs")
        p.add_argument("--gene-rx-dir", help="Folder with Gene→Reaction CSVs")
        p.add_argument("--met-rx-dir", help="Folder with Metabolite↔Reaction CSVs")
        p.add_argument("--rx-gpr-dir", help="Folder with Reaction→GPR CSVs")

    def handle(self, *args, **o):
        ingest_gene_experiments(
            experiment_index=o["experiment_index"],
            feature_index=o["feature_index"],
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
        self.stdout.write(self.style.SUCCESS("Gene experiment ingest finished."))
