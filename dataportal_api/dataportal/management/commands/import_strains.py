from __future__ import annotations
from django.core.management.base import BaseCommand

from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.strain.importers import (
    StrainContigImporter, DrugMICImporter, DrugMetabolismImporter
)
from dataportal.ingest.strain.parsers import read_mapping_tsv

class Command(BaseCommand):
    help = "Imports strains/contigs from FTP and (optionally) Drug MIC & Metabolism from local CSVs into a concrete ES index."

    def add_arguments(self, parser):
        parser.add_argument("--es-index", required=True, help="Concrete ES index (e.g., strain_index-2025.09.03)")

        # FTP strain/contigs
        parser.add_argument("--ftp-server", type=str, default="ftp.ebi.ac.uk")
        parser.add_argument("--ftp-directory", type=str, default="/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/")
        parser.add_argument("--map-tsv", type=str, default="../data-generators/data/gff-assembly-prefixes.tsv",
                            help="TSV with columns: assembly, prefix")
        parser.add_argument("--set-type-strains", nargs="+", help="e.g., BU_ATCC8492 PV_ATCC8482")

        # feature flags
        parser.add_argument("--include-mic", action="store_true")
        parser.add_argument("--include-metabolism", action="store_true")

        # local CSVs
        parser.add_argument("--mic-bu-file", type=str)
        parser.add_argument("--mic-pv-file", type=str)
        parser.add_argument("--metab-bu-file", type=str)
        parser.add_argument("--metab-pv-file", type=str)

    def handle(self, *args, **opts):
        es_index = opts["es_index"]
        repo = StrainIndexRepository(concrete_index=es_index)

        # 1) strains + contigs
        self.stdout.write(self.style.SUCCESS("Importing strains/contigs..."))
        mapping = read_mapping_tsv(opts["map_tsv"])
        StrainContigImporter(
            repo=repo,
            ftp_server=opts["ftp_server"],
            ftp_directory=opts["ftp_directory"],
            assembly_to_isolate=mapping,
            type_strains=opts.get("set_type_strains"),
        ).run()
        self.stdout.write(self.style.SUCCESS("Strains/contigs done."))

        # 2) MIC (optional)
        if opts["include_mic"]:
            self.stdout.write(self.style.SUCCESS("Importing Drug MIC..."))
            DrugMICImporter(
                repo=repo,
                bu_csv=opts.get("mic_bu_file"),
                pv_csv=opts.get("mic_pv_file"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Drug MIC done."))
        else:
            self.stdout.write(self.style.WARNING("Drug MIC skipped."))

        # 3) Metabolism (optional)
        if opts["include_metabolism"]:
            self.stdout.write(self.style.SUCCESS("Importing Drug Metabolism..."))
            DrugMetabolismImporter(
                repo=repo,
                bu_csv=opts.get("metab_bu_file"),
                pv_csv=opts.get("metab_pv_file"),
            ).run()
            self.stdout.write(self.style.SUCCESS("Drug Metabolism done."))
        else:
            self.stdout.write(self.style.WARNING("Drug Metabolism skipped."))

        self.stdout.write(self.style.SUCCESS("All imports finished."))
