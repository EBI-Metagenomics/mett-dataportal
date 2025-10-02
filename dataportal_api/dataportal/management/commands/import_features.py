import logging

from dataportal.ingest.feature.flows.essentiality import Essentiality
from dataportal.ingest.feature.flows.fitness import Fitness
from dataportal.ingest.feature.flows.gff_features import GFFGenes
from dataportal.ingest.feature.flows.mutant_growth import MutantGrowth
from dataportal.ingest.feature.flows.pooled_ttp import PooledTTP
from dataportal.ingest.feature.flows.protein_compound import ProteinCompound
from dataportal.ingest.feature.flows.proteomics import Proteomics
from dataportal.ingest.feature.flows.reactions import Reactions
from dataportal.ingest.utils import read_tsv_mapping, list_csv_files

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

from django.core.management.base import BaseCommand
import ftplib


class Command(BaseCommand):
    help = "Import features (genes + IG + analytics) into a versioned feature_index."

    def add_arguments(self, p):
        p.add_argument("--index", default="feature_index",
                       help="Target ES index (e.g. feature_index_v1)")

        p.add_argument("--ftp-server", default="ftp.ebi.ac.uk")
        p.add_argument("--ftp-root", default="/pub/databases/mett/annotations/v1_2024-04-15")
        p.add_argument("--isolates", nargs="*", help="If omitted, list from FTP")

        # NEW: mapping file for assembly prefixes
        p.add_argument(
            "--mapping-task-file",
            help="Path to gff-assembly-prefixes.tsv mapping file (prefix -> assembly)",
        )

        p.add_argument("--skip-core-genes", action="store_true",
                       help="Skip importing core gene features from GFFs")

        # Switch single-file inputs to directories so we can ingest *all* CSVs found
        p.add_argument("--essentiality-dir", help="Folder containing essentiality CSVs")
        p.add_argument("--fitness-dir", help="Folder containing fitness CSVs")
        p.add_argument("--proteomics-dir", help="Folder containing proteomics CSVs")
        p.add_argument("--protein-compound-dir", help="Folder with protein-compound CSVs")
        p.add_argument("--pooled-ttp-dir", help="Folder with pooled TTP CSVs")
        p.add_argument("--pool-metadata", help="Path to pool metadata CSV file")
        p.add_argument("--mutant-growth-dir", help="Folder with mutant growth CSVs")

        # Reactions need 3 sources; pass folders and we’ll iterate all CSVs in each
        p.add_argument("--gene-rx-dir", help="Folder with Gene→Reaction CSVs")
        p.add_argument("--met-rx-dir", help="Folder with Metabolite↔Reaction CSVs")
        p.add_argument("--rx-gpr-dir", help="Folder with Reaction→GPR CSVs")

    def handle(self, *args, **o):
        index_name = o["index"]

        # Mapping file (optional, but available for flows that may need it)
        mapping = {}
        if o.get("mapping_task_file"):
            mapping = read_tsv_mapping(
                o["mapping_task_file"],
                key_col="prefix",
                val_col="assembly",
                strip_suffix=".fa",
            )

        # isolates
        isolates = o["isolates"]
        if not isolates:
            ftp = ftplib.FTP(o["ftp_server"]);
            ftp.login()
            ftp.cwd(o["ftp_root"])
            # raw names from FTP
            raw_isolates = [n for n in ftp.nlst() if not n.startswith(".")]
            ftp.quit()
        else:
            raw_isolates = isolates

        # Use raw isolate names directly
        # 1) core genes (GFF) — can be skipped
        if not o.get("skip_core_genes"):
            # Pass raw names only
            GFFGenes(
                o["ftp_server"], o["ftp_root"], index_name=index_name, mapping=mapping
            ).run(raw_isolates=raw_isolates, norm_isolates=None)
        else:
            print("[import_features] Skipping core gene (GFF) import as requested.")

        # 2) Essentiality (process all CSVs in folder)
        ess_files = list_csv_files(o.get("essentiality_dir"))
        # print(f"[import_features] Essentiality CSVs found: {len(ess_files)}")
        for csv_path in ess_files:
            print(f"  - {csv_path}")
            Essentiality(index_name=index_name).run(csv_path)

        # 3) Fitness
        for csv_path in list_csv_files(o.get("fitness_dir")):
            Fitness(index_name=index_name).run(csv_path)

        # 4) Proteomics
        proteomics_files = list_csv_files(o.get("proteomics_dir"))
        # print(f"[import_features] Proteomics files found: {len(proteomics_files)}")
        for csv_path in proteomics_files:
            print(f"  - {csv_path}")
            Proteomics(index_name=index_name).run(csv_path)

        # 5) Protein–compound
        for csv_path in list_csv_files(o.get("protein_compound_dir")):
            ProteinCompound(index_name=index_name).run(csv_path)

        # 6) Pooled TTP
        for csv_path in list_csv_files(o.get("pooled_ttp_dir")):
            print(f"  - {csv_path}")
            PooledTTP(index_name=index_name, pool_metadata_path=o.get("pool_metadata")).run(csv_path)

        # 7) Reactions (cross-product of the three folders)
        gene_rx_files = list_csv_files(o.get("gene_rx_dir"))
        met_rx_files = list_csv_files(o.get("met_rx_dir"))
        rx_gpr_files = list_csv_files(o.get("rx_gpr_dir"))
        # print(f"[import_features] gene_rx: {len(gene_rx_files)} files")
        for f in gene_rx_files: print("  -", f)
        # print(f"[import_features] met_rx:  {len(met_rx_files)} files")
        for f in met_rx_files: print("  -", f)
        # print(f"[import_features] rx_gpr:  {len(rx_gpr_files)} files")
        for f in rx_gpr_files: print("  -", f)
        # run all combinations so you don't depend on strict naming;
        # if you prefer pairing by filename stem, we can add that too.
        for gr in gene_rx_files:
            for mr in met_rx_files:
                for gp in rx_gpr_files:
                    Reactions(index_name=index_name).run(gr, mr, gp)

        # 8) Mutant growth
        for csv_path in list_csv_files(o.get("mutant_growth_dir")):
            MutantGrowth(index_name=index_name).run(csv_path)
